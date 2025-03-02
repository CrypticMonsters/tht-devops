import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import boto3
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel

# Define Prometheus metrics
REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

ORDER_PROCESSING_TOTAL = Counter(
    "order_processing_total", "Total number of orders processed", ["status"]
)

INVENTORY_LEVEL = Gauge(
    "inventory_stock_level", "Current stock level for each product", ["product_id"]
)

INVENTORY_OPERATIONS_TOTAL = Counter(
    "inventory_operations_total",
    "Total number of inventory operations",
    ["operation", "status"],
)

DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", None)
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "inventory")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


app = FastAPI(title="Order Processor")

dynamodb = boto3.resource("dynamodb", endpoint_url=DYNAMODB_ENDPOINT)

inventory_table = dynamodb.Table(DYNAMODB_TABLE)


class OrderRequest(BaseModel):
    product_id: str
    quantity: int
    customer_id: str


class ProcessedOrder(BaseModel):
    status: str
    total_price: int
    processed_at: str


class InventoryRepository:
    def __init__(self):
        self.table = inventory_table

    async def check_and_update_inventory(
        self, product_id: str, quantity: int
    ) -> Optional[int]:
        try:
            response = self.table.get_item(Key={"product_id": product_id})
            INVENTORY_OPERATIONS_TOTAL.labels(operation="get", status="success").inc()

            item = response.get("Item")
            if not item or item["stock"] < quantity:
                logger.error(
                    f"Insufficient stock for product {product_id}",
                )
                INVENTORY_OPERATIONS_TOTAL.labels(
                    operation="check", status="insufficient_stock"
                ).inc()
                return None

            current_stock = item["stock"]
            INVENTORY_LEVEL.labels(product_id=product_id).set(current_stock)

            self.table.update_item(
                Key={"product_id": product_id},
                UpdateExpression="SET stock = stock - :quantity",
                ExpressionAttributeValues={":quantity": quantity},
            )
            INVENTORY_OPERATIONS_TOTAL.labels(
                operation="update", status="success"
            ).inc()
            INVENTORY_LEVEL.labels(product_id=product_id).set(current_stock - quantity)

            return int(item["price"] * quantity)

        except Exception as e:
            logger.error(
                f"Inventory operation failed: {str(e)}",
            )
            INVENTORY_OPERATIONS_TOTAL.labels(operation="update", status="error").inc()
            raise HTTPException(status_code=500, detail="Inventory operation failed")


@app.on_event("startup")
async def startup_event():
    logger.info("Application started")


@app.post("/process-order", response_model=ProcessedOrder)
async def process_order(order: OrderRequest, request: Request):
    logger.info(
        f"Processing order for product {order.product_id}",
    )

    repository = InventoryRepository()
    total_price = await repository.check_and_update_inventory(
        order.product_id, order.quantity
    )

    if total_price is None:
        ORDER_PROCESSING_TOTAL.labels(status="insufficient_stock").inc()
        raise HTTPException(status_code=400, detail="Insufficient inventory")

    ORDER_PROCESSING_TOTAL.labels(status="success").inc()
    return ProcessedOrder(
        status="confirmed",
        total_price=total_price,
        processed_at=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/health")
async def health_check():
    try:
        inventory_table.scan(Limit=1)

        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database is unhealthy: {str(e)}")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    method = request.method
    path = request.url.path

    # Record request duration
    with REQUEST_DURATION.labels(
        method=method,
        endpoint=path,
    ).time():
        response = await call_next(request)

    # Update request count
    REQUESTS_TOTAL.labels(
        method=method, endpoint=path, status=response.status_code
    ).inc()

    return response


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
