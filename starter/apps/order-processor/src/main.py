from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import boto3
import logging
import os

from datetime import datetime, timezone
from typing import Dict, Any, Optional

DYNAMODB_ENDPOINT=os.getenv("DYNAMODB_ENDPOINT", None)
DYNAMODB_TABLE=os.getenv("DYNAMODB_TABLE", "inventory")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


app = FastAPI(title="Order Processor")

dynamodb = boto3.resource(
    "dynamodb", endpoint_url=DYNAMODB_ENDPOINT)

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
    
            item = response.get("Item")
            if not item or item["stock"] < quantity:
                logger.error(
                    f"Insufficient stock for product {product_id}",
                )
                return None
    
            self.table.update_item(
                Key={"product_id": product_id},
                UpdateExpression="SET stock = stock - :quantity",
                ExpressionAttributeValues={":quantity": quantity},
            )
    
            return int(item["price"] * quantity)
    
        except Exception as e:
            logger.error(
                f"Inventory operation failed: {str(e)}",
            )
            raise HTTPException(
                status_code=500, detail="Inventory operation failed"
            )



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
        raise HTTPException(status_code=400, detail="Insufficient inventory")

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
