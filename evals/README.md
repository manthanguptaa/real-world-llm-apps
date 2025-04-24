# 🧠 Evals - LLM as a Judge

> Harness the power of LLMs to evaluate LLM outputs with objective, consistent criteria

Evals provides a simple yet powerful way to evaluate AI-generated content using state-of-the-art large language models. Whether you're comparing model versions, tuning prompts, or assessing content quality, Evals gives you reliable, consistent metrics with minimal setup.

https://github.com/user-attachments/assets/3607eda9-9bba-45d1-b760-0eb448bc5a35

## ✨ Key Features

- **Customizable Criteria** - Define exactly what aspects of responses you want to evaluate
- **Consistent Scoring** - Get reliable 1-5 scale ratings across multiple dimensions
- **Detailed Reasoning** - Understand exactly why each score was assigned
- **Batch Processing** - Evaluate hundreds of examples efficiently
- **Rich Analytics** - Generate statistical summaries and visualizations
- **Simple Integration** - Just a few lines of code to get started

## 🚀 Quick Setup

```bash
# 1. Clone the repository
git clone git@github.com:manthanguptaa/real-world-llm-apps.git
cd evals

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your OpenAI API key in a .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env

# 5. Run the example
python example.py
```

> 💡 Make sure to replace `your_api_key_here` with your actual OpenAI API key. You can get one from [OpenAI's platform](https://platform.openai.com/api-keys).

## 📊 Usage Examples

### Basic Evaluation

```python
from evals import Evals

# Create evaluator with custom criteria
evaluator = Evals(
    model="gpt-4o",
    criteria={
        "accuracy": "Is the information accurate and factual?",
        "relevance": "Is the response relevant to the query?",
        "completeness": "Does the response address all aspects of the query?"
    }
)

# Evaluate a single response
result = evaluator.evaluate(
    query="What is machine learning?",
    response="Machine learning is a type of artificial intelligence.",
    reference="Machine learning is a field of AI where computer systems learn from data to make decisions without explicit programming."
)

# View the results
print(f"Overall score: {result.overall_score():.2f}/5.0")
for criterion, score in result.scores.items():
    reason = result.reasoning.get(criterion, "")
    print(f"{criterion}: {score}/5 - {reason}")
```

### Process Multiple Examples & Create Visualizations

```python
# Batch evaluate multiple examples
evaluations = evaluator.evaluate_batch([
    {
        "query": "What's the capital of France?",
        "response": "Paris is the capital of France.",
        "reference": "Paris is the capital and most populous city of France."
    },
    # Add more examples...
])

# Generate summary statistics
scores = evaluator.calculate_scores(evaluations)
print(f"Overall mean score: {scores['overall']['mean']:.2f}/5.0")

# Export to CSV for further analysis
df = evaluator.to_dataframe(evaluations)
df.to_csv('evaluation_results.csv', index=False)

# Create visualization
fig = evaluator.plot_scores(evaluations)
fig.savefig('score_distribution.png', dpi=300)
```

## 💡 Use Cases

- **Model Comparison**: Benchmark different models against the same prompts
- **Prompt Engineering**: Test variations of prompts to see which performs best
- **Quality Assurance**: Ensure AI outputs meet your quality standards
- **Content Assessment**: Evaluate factuality and quality of generated content
- **Fine-tuning Feedback**: Generate targeted feedback for model improvement

## 🛠️ Advanced Options

```python
# Use a different model or custom criteria
evaluator = Evals(
    model="gpt-4-turbo",
    temperature=0.2,
    scale=10,  # Use a 10-point scale instead of default 5
    criteria={
        "accuracy": "Is the information accurate and factual?",
        "clarity": "Is the explanation clear and easy to understand?",
        "depth": "Does the response provide sufficient depth on the topic?",
        "engagement": "Is the response engaging and interesting to read?",
        "creativity": "Does the response demonstrate creative thinking?"
    }
)
```

## 🔍 Example

Run the included example:

```bash
python example.py
```

This will evaluate several example responses, print detailed scores with reasoning, and save results to both a CSV file and visualization.
