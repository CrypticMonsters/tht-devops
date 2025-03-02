# service_a/src/main.py
import logging
import os
import random
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

import boto3
import dns.resolver
import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Define Prometheus metrics
REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ORDER_CREATION_TOTAL = Counter(
    'order_creation_total',
    'Total number of orders created',
    ['status']
)

def resolve_srv(endpoint):
    srvInfo = {}
    srv_records=dns.resolver.query(endpoint, 'SRV')
    srv = random.choice(srv_records)
    srvInfo['weight']   = srv.weight
    srvInfo['host']     = str(srv.target).rstrip('.')
    srvInfo['port']     = srv.port
    srvInfo['priority'] = srv.priority
    
    return f"http://{srvInfo['host']}:{srvInfo['port']}"
    

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [- %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Order API Gateway")

SRV_ENDPOINT = os.getenv("SRV_ENDPOINT", None)
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", None)

DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "orders")

ORDER_PROCESSOR_URL = os.getenv("ORDER_PROCESSOR_URL", "http://localhost:8001")

dynamodb = boto3.resource("dynamodb", endpoint_url=DYNAMODB_ENDPOINT)
orders_table = dynamodb.Table(DYNAMODB_TABLE)


class Order(BaseModel):
    product_id: str
    quantity: int
    customer_id: str


class OrderResponse(BaseModel):
    order_id: str
    product_id: str
    quantity: int
    customer_id: str
    status: str
    processed_at: str
    created_at: str
    total_price: Optional[int] = None


class OrderRepository:
    def __init__(self):
        self.table = orders_table

    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = self.table.put_item(Item=order_data)
            return order_data
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            raise HTTPException(status_code=500, detail="Database operation failed")

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.table.get_item(Key={"order_id": order_id})
            return response.get("Item")
        except Exception as e:
            logger.error(f"Failed to get order: {str(e)}")
            raise HTTPException(status_code=500, detail="Database operation failed")


@app.on_event("startup")
async def startup_event():
    logger.info("Application started")


@app.post("/orders/", response_model=OrderResponse)
async def create_order(order: Order, request: Request):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ORDER_PROCESSOR_URL}/process-order",
                json=order.dict(),
                timeout=5.0,
            )

            if response.status_code == 200:
                processed_order = response.json()
                order.quantity=Decimal(str(order.quantity))
                order_data = {
                    "order_id": str(uuid.uuid4()),
                    **order.dict(),
                    **processed_order,
                    "created_at": datetime.utcnow().isoformat(),
                }

                repository = OrderRepository()
                stored_order = await repository.create_order(order_data)
                ORDER_CREATION_TOTAL.labels(status="success").inc()
                return OrderResponse(**stored_order)
            else:
                logger.error(
                    f"Order Processor returned error: {response.text}",
                )
                ORDER_CREATION_TOTAL.labels(status="processor_error").inc()
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )

    except httpx.TimeoutException:
        ORDER_CREATION_TOTAL.labels(status="timeout").inc()
        raise HTTPException(status_code=504, detail="Order Processor timeout")
    except Exception as e:
        logger.error(
            f"Order processing failed: {str(e)}",
        )
        ORDER_CREATION_TOTAL.labels(status="error").inc()
        raise HTTPException(status_code=500, detail="Order processing failed")


@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, request: Request):

    repository = OrderRepository()

    order = await repository.get_order(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse(**order)


@app.get("/health")
async def health_check():
    try:
        global ORDER_PROCESSOR_URL

        orders_table.scan(Limit=1)

        if SRV_ENDPOINT: 
            ORDER_PROCESSOR_URL = resolve_srv(SRV_ENDPOINT)

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ORDER_PROCESSOR_URL}/health", timeout=2.0)
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="Orders Processor unhealthy")

        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


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
        method=method,
        endpoint=path,
        status=response.status_code
    ).inc()
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

