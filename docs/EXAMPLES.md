# A4E Agent Examples

This document provides example patterns for building different types of conversational AI agents.

## Example 1: Nutrition Coach Agent

A fitness and health agent that helps users track nutrition and calculate health metrics.

### Create the Agent

```bash
a4e init --name nutrition-coach --display-name "Nutrition Coach" \
  --description "Personalized nutrition and fitness guidance" \
  --category "Fitness & Health" --template basic --yes
cd nutrition-coach
```

### Add Tools

```bash
# BMI Calculator
a4e add tool calculate_bmi -d "Calculate Body Mass Index from weight and height"

# Calorie Calculator
a4e add tool calculate_calories -d "Calculate daily calorie needs based on activity level"

# Food Search
a4e add tool search_food -d "Search for nutritional information about foods"
```

**Implementation** (`tools/calculate_bmi.py`):
```python
from a4e.sdk import tool
from typing import Optional

@tool
def calculate_bmi(
    weight_kg: float,
    height_m: float,
) -> dict:
    """Calculate Body Mass Index from weight and height"""
    bmi = weight_kg / (height_m ** 2)

    # Determine category
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    return {
        "status": "success",
        "bmi": round(bmi, 1),
        "category": category,
        "weight_kg": weight_kg,
        "height_m": height_m
    }
```

### Add Views

```bash
# BMI Result View
a4e add view bmi-result -d "Display BMI calculation results with category"

# Calorie Result View
a4e add view calorie-result -d "Display daily calorie recommendations"
```

**Implementation** (`views/bmi-result/view.tsx`):
```tsx
"use client";
import React from "react";

interface BmiResultProps {
  bmi: number;
  category: string;
  weight_kg: number;
  height_m: number;
}

export default function BmiResultView(props: BmiResultProps) {
  const { bmi, category, weight_kg, height_m } = props;

  const getCategoryColor = () => {
    switch (category) {
      case "Normal": return "text-green-600";
      case "Underweight": return "text-yellow-600";
      default: return "text-red-600";
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-4">Your BMI Results</h2>

      <div className="text-center mb-6">
        <span className="text-5xl font-bold">{bmi}</span>
        <p className={`text-lg font-medium ${getCategoryColor()}`}>
          {category}
        </p>
      </div>

      <div className="text-sm text-gray-600">
        <p>Weight: {weight_kg} kg</p>
        <p>Height: {height_m} m</p>
      </div>
    </div>
  );
}
```

### Add Skills

```bash
# BMI Skill
a4e add skill calculate_bmi_skill --name "Calculate BMI" \
  --view bmi-result --triggers "calculate bmi,check my bmi,what is my bmi" \
  --tools calculate_bmi

# Calorie Skill
a4e add skill calculate_calories_skill --name "Calculate Calories" \
  --view calorie-result --triggers "how many calories,daily calories,calorie needs"
```

---

## Example 2: E-commerce Assistant

A shopping assistant that helps users find and compare products.

### Create the Agent

```bash
a4e init --name shop-assistant --display-name "Shop Assistant" \
  --description "Your personal shopping companion" \
  --category "E-commerce" --template full --yes
cd shop-assistant
```

### Add Tools

```bash
a4e add tool search_products -d "Search for products by query and filters"
a4e add tool get_product_details -d "Get detailed information about a product"
a4e add tool compare_products -d "Compare multiple products side by side"
a4e add tool add_to_cart -d "Add a product to the shopping cart"
```

**Implementation** (`tools/search_products.py`):
```python
from a4e.sdk import tool
from typing import Optional, List

@tool
def search_products(
    query: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: Optional[int] = 10,
) -> dict:
    """Search for products by query and filters"""
    # Mock implementation - replace with actual API call
    products = [
        {
            "id": "prod_001",
            "name": f"Product matching '{query}'",
            "price": 29.99,
            "rating": 4.5,
            "image_url": "https://example.com/product.jpg"
        }
    ]

    return {
        "status": "success",
        "products": products,
        "total": len(products),
        "query": query
    }
```

### Add Views

```bash
a4e add view product-grid -d "Display products in a grid layout"
a4e add view product-detail -d "Show detailed product information"
a4e add view comparison-table -d "Compare products in a table"
a4e add view cart-summary -d "Show shopping cart contents"
```

### Add Skills

```bash
a4e add skill search_products_skill --name "Search Products" \
  --view product-grid --triggers "search for,find products,show me" \
  --tools search_products

a4e add skill view_product_skill --name "View Product" \
  --view product-detail --triggers "show product,product details,more info" \
  --tools get_product_details

a4e add skill compare_skill --name "Compare Products" \
  --view comparison-table --triggers "compare,which is better,difference between" \
  --tools compare_products
```

---

## Example 3: Customer Support Bot

A support agent that helps users with common issues and escalates when needed.

### Create the Agent

```bash
a4e init --name support-bot --display-name "Support Bot" \
  --description "24/7 customer support assistant" \
  --category "Customer Support" --template basic --yes
cd support-bot
```

### Add Tools

```bash
a4e add tool search_faq -d "Search frequently asked questions"
a4e add tool get_order_status -d "Check the status of an order"
a4e add tool create_ticket -d "Create a support ticket for escalation"
a4e add tool get_return_policy -d "Get return and refund policy information"
```

### Add Views

```bash
a4e add view faq-results -d "Display FAQ search results"
a4e add view order-status -d "Show order tracking information"
a4e add view ticket-created -d "Confirmation of support ticket"
a4e add view policy-info -d "Display policy information"
```

### Add Skills

```bash
a4e add skill faq_skill --name "FAQ Search" \
  --view faq-results --triggers "how do i,what is,help with" \
  --tools search_faq

a4e add skill order_status_skill --name "Order Status" \
  --view order-status --triggers "where is my order,track order,order status" \
  --tools get_order_status --auth

a4e add skill escalate_skill --name "Create Ticket" \
  --view ticket-created --triggers "speak to human,escalate,create ticket" \
  --tools create_ticket --auth
```

---

## Example 4: Education Tutor

An educational assistant that helps students learn and practice.

### Create the Agent

```bash
a4e init --name math-tutor --display-name "Math Tutor" \
  --description "Interactive math learning assistant" \
  --category "Education" --template full --yes
cd math-tutor
```

### Add Tools

```bash
a4e add tool generate_problem -d "Generate a math problem based on topic and difficulty"
a4e add tool check_answer -d "Check if the student's answer is correct"
a4e add tool explain_concept -d "Explain a mathematical concept"
a4e add tool get_hint -d "Provide a hint for the current problem"
```

### Add Views

```bash
a4e add view problem-display -d "Display a math problem with input"
a4e add view answer-feedback -d "Show feedback on the student's answer"
a4e add view concept-explanation -d "Display concept explanation with examples"
a4e add view progress-dashboard -d "Show learning progress and statistics"
```

### Add Skills

```bash
a4e add skill practice_skill --name "Practice Problems" \
  --view problem-display --triggers "practice,give me a problem,test me" \
  --tools generate_problem

a4e add skill explain_skill --name "Explain Concept" \
  --view concept-explanation --triggers "explain,how does,what is" \
  --tools explain_concept

a4e add skill check_answer_skill --name "Check Answer" \
  --view answer-feedback --triggers "check,is this right,my answer is" \
  --tools check_answer
```

---

## Patterns & Best Practices

### Tool Design Patterns

1. **Single Responsibility**: Each tool should do one thing well
2. **Clear Return Types**: Always return a dict with `status` and relevant data
3. **Error Handling**: Return `{"status": "error", "message": "..."}` on failure
4. **Type Hints**: Always include type hints for parameters

```python
@tool
def my_tool(
    required_param: str,
    optional_param: Optional[int] = 10,
) -> dict:
    """Clear description of what this tool does"""
    try:
        # Implementation
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### View Design Patterns

1. **Responsive Design**: Use Tailwind classes for responsive layouts
2. **Loading States**: Handle loading and error states
3. **Accessibility**: Include proper ARIA labels and semantic HTML
4. **Consistent Styling**: Follow design system conventions

```tsx
interface MyViewProps {
  data: SomeType;
  loading?: boolean;
  error?: string;
}

export default function MyView({ data, loading, error }: MyViewProps) {
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Content */}
    </div>
  );
}
```

### Skill Design Patterns

1. **Clear Intent Triggers**: Use natural phrases users would actually say
2. **Fallback Skills**: Create catch-all skills for unmatched intents
3. **Authentication**: Mark skills requiring auth with `requires_auth`
4. **Tool Chaining**: Skills can call multiple tools in sequence

---

## Testing Your Agent

### Validate Before Testing

```bash
a4e validate
```

### Start Development Server

```bash
a4e dev start
```

### Test Flow

1. Open the ngrok URL in browser
2. Test each skill by typing trigger phrases
3. Verify views render correctly
4. Check tool return values in console

### Common Issues

- **View not rendering**: Check props match schema
- **Tool not called**: Verify intent triggers
- **Schema errors**: Run `a4e validate` for details
