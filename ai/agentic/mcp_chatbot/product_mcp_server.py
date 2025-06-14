from typing import List
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("product")


product_catalog = [
    {
        "product_id": "P001",
        "name": "Essence",
        "description": "A stylish sneaker suitable for various occasions.",
        "category": "Lifestyle",
        "price": 100.00,
    },
    {
        "product_id": "P002",
        "name": "Stride",
        "description": "A versatile sneaker for everyday runners.",
        "category": "Running",
        "price": 120.00,
    },
    {
        "product_id": "P003",
        "name": "Impulse",
        "description": "Flexible training shoes designed for athletes.",
        "category": "Training",
        "price": 140.00,
    },
    {
        "product_id": "P004",
        "name": "Forge",
        "description": "Durable training shoes built for performance and lifting.",
        "category": "Training",
        "price": 160.00,
    },
]


@mcp.resource("catalog://categories")
def get_product_categories() -> str:
    """
    This resource provides a simple list of all available Product categories.

    Args:
        None
    Returns:
        A markdown formatted string containing all product categories.
    """
    # Get all the categories from the product catalog
    categories = set()
    for product in product_catalog:
        categories.add(product["category"])

    # Create markdown content
    content = "# Available Product Categories\n\n"
    if categories:
        for category in sorted(categories):
            content += f"- {category}\n"
    else:
        content += "No categories found.\n"
    return content


@mcp.resource("catalog://{category}")
def get_product_category(category: str) -> str:
    """
    Get list of products in a specific category.

    Args:
        category: The product category to retrieve products for
    Returns:
        A markdown formatted string containing product details in the category.
    """
    # Normalize category name
    category = category.lower().strip()

    # Filter products by category
    products = [
        p for p in product_catalog if p["category"].lower() == category
    ]

    if not products:
        return f"# No products found in category: {category}"

    # Create markdown content with product details
    content = f"# Products in {category.title()} Category\n\n"
    content += f"Total products: {len(products)}\n\n"

    for product in products:
        content += f"## {product['name']}\n"
        content += f"- **Product ID**: {product['product_id']}\n"
        content += f"- **Price**: ${product['price']:.2f}\n"
        content += f"- **Description**: {product['description']}\n\n"
        content += "---\n\n"

    return content


@mcp.tool()
def search_products(
    category: str = None, size: str = None, color: str = None
) -> List[dict]:
    """
    Search for products based on category, size, and color preferences.

    Args:
        category: Product category (Lifestyle, Running, Training)
        size: Shoe size
        color: Preferred color
    Returns:
        List of matching products with their details and availability
    """
    product_stock = {
        "P001": [
            {"color": "Black", "size": "8", "quantity": 20},
            {"color": "Black", "size": "9", "quantity": 15},
            {"color": "White", "size": "8", "quantity": 30},
            {"color": "White", "size": "9", "quantity": 15},
            {"color": "Red", "size": "10", "quantity": 20},
        ],
        "P002": [
            {"color": "Black", "size": "8", "quantity": 10},
            {"color": "Black", "size": "9", "quantity": 5},
            {"color": "White", "size": "8", "quantity": 20},
            {"color": "Red", "size": "10", "quantity": 10},
            {"color": "Green", "size": "10", "quantity": 15},
        ],
        "P003": [
            {"color": "Black", "size": "8", "quantity": 5},
            {"color": "Black", "size": "9", "quantity": 10},
            {"color": "White", "size": "9", "quantity": 15},
            {"color": "Red", "size": "11", "quantity": 5},
            {"color": "Green", "size": "10", "quantity": 10},
        ],
        "P004": [
            {"color": "Black", "size": "8", "quantity": 8},
            {"color": "White", "size": "9", "quantity": 12},
            {"color": "White", "size": "11", "quantity": 18},
            {"color": "Blue", "size": "10", "quantity": 7},
            {"color": "Blue", "size": "9", "quantity": 12},
        ],
    }

    results = []

    # Step 1: Filter products by category first if specified
    filtered_products = product_catalog
    if category:
        filtered_products = [
            p
            for p in product_catalog
            if p["category"].lower() == category.lower()
        ]

    # Step 2: For each filtered product, check inventory and apply size/color filters
    for product in filtered_products:
        product_id = product["product_id"]

        # Get inventory for this product
        inventory = product_stock.get(product_id, [])

        # Apply size and color filters to inventory
        matching_inventory = inventory

        if size:
            matching_inventory = [
                item
                for item in matching_inventory
                if item["size"] == str(size)
            ]

        if color:
            matching_inventory = [
                item
                for item in matching_inventory
                if item["color"].lower() == color.lower()
            ]

        # Only include products that have matching inventory
        if matching_inventory:
            product_result = product.copy()
            product_result["available_options"] = matching_inventory
            product_result["total_available"] = sum(
                item["quantity"] for item in matching_inventory
            )
            results.append(product_result)

    return results


@mcp.prompt()
def product_recommendation_prompt(
    customer_needs: str = "",
    category: str = "",
    size: str = "",
    color: str = "",
) -> str:
    """
    Generate product recommendations based on customer needs.

    Args:
        customer_needs: What the customer described they need
        category: Product category they're interested in
        size: Preferred shoe size
        color: Preferred color

    Returns:
        A prompt to help recommend products with available tools and resources.
    """

    prompt = f"""You are helping a customer find shoes. Here's what they've told you:

Customer needs: {customer_needs}
Category preference: {category or "Not specified"}
Size preference: {size or "Not specified"}
Color preference: {color or "Not specified"}

Your task:
1. If category is specified, use the catalog://{category.lower()} resource to see available products
2. Use the search_products tool to find matching shoes based on their preferences
3. For any specific products you want to recommend, use check_product_inventory to verify availability
4. Present the options in a friendly, conversational way
5. If they haven't specified size or color, ask for those details

Be helpful and guide them toward making a decision!"""

    return prompt


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
