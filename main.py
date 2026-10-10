
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("Orders")


def create_order():
    print("\n--- CREATE ORDER ---")

    order_id = input("Enter Order ID: ").strip()
    customer_id = input("Enter Customer ID: ").strip()
    date = input("Enter Order Date (YYYY-MM-DD): ").strip()
    item = input("Enter Item Name: ").strip()

# Validate the date format and actual calendar date
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print("Invalid date. Use YYYY-MM-DD, e.g. 2026-10-11.")
        return

    if not item:
        print("Item name cannot be empty.")
        return

    try:
        quantity = int(input("Enter Quantity: "))
        amount = Decimal(input("Enter Amount: "))

        if quantity <= 0:
            print("Quantity must be greater than zero.")
            return

        if not amount.is_finite() or amount < 0:
            print("Amount must be a valid, non-negative number.")
            return


        if not order_id or not customer_id or not date or not item:
            print("All fields are required.")
            return

        if quantity <= 0 or amount < 0:
            print("Quantity must be positive and amount cannot be negative.")
            return

        table.put_item(
            Item={
                "OrderID": order_id,
                "CustomerID": customer_id,
                "Date": date,
                "Item": item,
                "Quantity": quantity,
                "Amount": amount
            },
            ConditionExpression=(
                "attribute_not_exists(OrderID) "
                "AND attribute_not_exists(CustomerID)"
            )
        )

        print("Order created successfully!")

    except ValueError:
        print("Invalid quantity or amount.")
    except Exception as error:
        print("Could not create order:", error)


def read_order():
    print("\n--- READ ORDER ---")

    order_id = input("Enter Order ID: ").strip()
    customer_id = input("Enter Customer ID: ").strip()

    try:
        response = table.get_item(
            Key={
                "OrderID": order_id,
                "CustomerID": customer_id
            }
        )

        order = response.get("Item")

        if order:
            print("\nOrder Details:")
            for key, value in order.items():
                print(f"{key}: {value}")
        else:
            print("Order not found.")

    except Exception as error:
        print("Could not retrieve order:", error)



def update_order():
    print("\n--- UPDATE ORDER ---")

    order_id = input("Enter Order ID: ").strip()
    customer_id = input("Enter Customer ID: ").strip()

    if not order_id or not customer_id:
        print("Order ID and Customer ID cannot be empty.")
        return

    try:
        # Check whether the order exists
        response = table.get_item(
            Key={
                "OrderID": order_id,
                "CustomerID": customer_id
            }
        )

        if "Item" not in response:
            print("Order not found. Nothing was updated.")
            return

        print("\nChoose the field to update:")
        print("1. Item Name")
        print("2. Quantity")
        print("3. Amount")

        choice = input("Enter your choice (1-3): ").strip()

        if choice == "1":
            field = "Item"
            value = input("Enter new item name: ").strip()

            if not value:
                print("Item name cannot be empty.")
                return

        elif choice == "2":
            field = "Quantity"

            try:
                value = int(input("Enter new quantity: "))
                if value <= 0:
                    print("Quantity must be greater than zero.")
                    return
            except ValueError:
                print("Quantity must be a whole number.")
                return

        elif choice == "3":
            field = "Amount"

            try:
                value = Decimal(input("Enter new amount: "))

                if not value.is_finite() or value < 0:
                    print("Amount must be a valid, non-negative number.")
                    return

            except Exception:
                print("Enter a valid amount.")
                return

        else:
            print("Invalid choice.")
            return

        # Update only if the order still exists
        result = table.update_item(
            Key={
                "OrderID": order_id,
                "CustomerID": customer_id
            },
            UpdateExpression="SET #field = :value",
            ExpressionAttributeNames={
                "#field": field
            },
            ExpressionAttributeValues={
                ":value": value
            },
            ConditionExpression="attribute_exists(OrderID)",
            ReturnValues="UPDATED_NEW"
        )

        print("\nOrder updated successfully!")
        print("Updated values:", result["Attributes"])

    except Exception as error:
        print("Could not update order:", error)



def query_orders():
    print("\n--- QUERY ORDERS ---")

    order_id = input("Enter Order ID to search: ").strip()

    try:
        response = table.query(
            KeyConditionExpression=Key("OrderID").eq(order_id)
        )

        orders = response["Items"]

        if orders:
            for order in orders:
                print("\n", order)
        else:
            print("No orders found for that Order ID.")

    except Exception as error:
        print("Could not query orders:", error)



def delete_order():
    print("\n--- DELETE ORDER ---")

    order_id = input("Enter Order ID: ").strip()
    customer_id = input("Enter Customer ID: ").strip()

    if not order_id or not customer_id:
        print("Order ID and Customer ID cannot be empty.")
        return

    try:
        # Check whether the order exists first
        response = table.get_item(
            Key={
                "OrderID": order_id,
                "CustomerID": customer_id
            }
        )

        order = response.get("Item")

        if not order:
            print("Order not found. Nothing was deleted.")
            return

        print("\nOrder to be deleted:")
        print(f"Order ID: {order_id}")
        print(f"Customer ID: {customer_id}")
        print(f"Item: {order.get('Item', '-')}")
        print(f"Amount: {order.get('Amount', '-')}")

        confirm = input(
            "\nAre you sure you want to delete this order? (yes/no): "
        ).strip().lower()

        if confirm != "yes":
            print("Deletion cancelled.")
            return

        table.delete_item(
            Key={
                "OrderID": order_id,
                "CustomerID": customer_id
            },
            ConditionExpression="attribute_exists(OrderID)"
        )

        print("Order deleted successfully!")

    except Exception as error:
        print("Could not delete order:", error)



def view_all_orders():
    print("\n--- ALL ORDERS ---")

    try:
        response = table.scan()
        orders = response["Items"]

        # Continue fetching if DynamoDB returns a paginated response
        while "LastEvaluatedKey" in response:
            response = table.scan(
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            orders.extend(response["Items"])

        if not orders:
            print("No orders found.")
            return

        orders.sort(key=lambda order: order["OrderID"])

        print(
            f"\n{'ORDER ID':<15} {'CUSTOMER ID':<15} "
            f"{'DATE':<12} {'ITEM':<20} {'QTY':>5} {'AMOUNT':>12}"
        )
        print("-" * 85)

        for order in orders:
            print(
                f"{order['OrderID']:<15} "
                f"{order['CustomerID']:<15} "
                f"{order.get('Date', '-'):<12} "
                f"{order.get('Item', '-'):<20} "
                f"{order.get('Quantity', 0):>5} "
                f"{str(order.get('Amount', 0)):>12}"
            )

        print(f"\nTotal orders: {len(orders)}")

    except Exception as error:
        print("Could not retrieve orders:", error)


def search_by_customer():
    print("\n--- SEARCH ORDERS BY CUSTOMER ID ---")

    customer_id = input("Enter Customer ID: ").strip()

    if not customer_id:
        print("Customer ID cannot be empty.")
        return

    try:
        response = table.query(
            IndexName="CustomerID-index",
            KeyConditionExpression=Key("CustomerID").eq(customer_id)
        )

        orders = response["Items"]

        if orders:
            print(f"\nOrders for customer {customer_id}:")
            for order in orders:
                print("-" * 35)
                print(f"Order ID:  {order['OrderID']}")
                print(f"Date:      {order.get('Date', '-')}")
                print(f"Item:      {order.get('Item', '-')}")
                print(f"Quantity:  {order.get('Quantity', '-')}")
                print(f"Amount:    {order.get('Amount', '-')}")
            print(f"\nTotal orders found: {len(orders)}")
        else:
            print("No orders found for this customer.")

    except Exception as error:
        print("Customer search failed:", error)

def main():
    while True:
        print("\n===== E-COMMERCE ORDER MANAGEMENT SYSTEM =====")
        print("1. Create Order")
        print("2. Read Order")
        print("3. Update Order")
        print("4. Query Orders by Order ID")
        print("5. Delete Order")
        print("6. View All Orders")
        print("7. Search Orders by Customer ID")
        print("8. Exit")

        choice = input("Enter your choice (1-8): ").strip()

        if choice == "1":
            create_order()
        elif choice == "2":
            read_order()
        elif choice == "3":
            update_order()
        elif choice == "4":
            query_orders()
        elif choice == "5":
            delete_order()
        elif choice == "6":
            view_all_orders()
        elif choice == "7":
            search_by_customer()
        elif choice == "8":
            print("Exiting application.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
