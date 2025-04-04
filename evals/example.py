#!/usr/bin/env python3
"""
Basic example of using the Evals class to evaluate LLM responses.
"""

import os
import json
from dotenv import load_dotenv
from evals import Evals

# Load environment variables (including API key)
load_dotenv()

# Example data
EXAMPLES = [
    {
        "query": "What are the benefits of regular exercise?",
        "response": "Regular exercise helps strengthen muscles and improve cardiovascular health.",
        "reference": "Regular exercise offers numerous benefits including improved cardiovascular health, increased strength, better mood, weight management, and reduced risk of chronic diseases."
    },
    {
        "query": "Explain how photosynthesis works.",
        "response": "Photosynthesis is the process where plants use sunlight to convert carbon dioxide and water into glucose and oxygen.",
        "reference": "Photosynthesis is the process by which green plants, algae, and some bacteria convert light energy, usually from the sun, into chemical energy stored in glucose and other organic compounds. During this process, carbon dioxide and water are converted into glucose and oxygen is released as a byproduct."
    },
    {
        "query": "What is the capital of France?",
        "response": "The capital of France is Paris.",
        "reference": "Paris is the capital and most populous city of France."
    }
]

def main():
    """Run a basic evaluation example."""
    
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OpenAI API key not found!")
        print("Please set your OPENAI_API_KEY environment variable")
        return
    
    # Create evaluator with custom criteria
    evaluator = Evals(
        model="gpt-4o",
        criteria={
            "accuracy": "Is the information provided in the response accurate and factual?",
            "completeness": "Does the response address all aspects of the query comprehensively?",
            "clarity": "Is the response clear, coherent, and easy to understand?",
        }
    )
    
    print(f"Evaluating {len(EXAMPLES)} examples...")
    
    # Evaluate all examples
    evaluations = evaluator.evaluate_batch(EXAMPLES)
    
    # Print results for each evaluation
    for i, result in enumerate(evaluations):
        print(f"\nExample {i+1}:")
        print(f"Query: {result.query}")
        print(f"Response: {result.response}")
        print(f"Overall score: {result.overall_score():.2f}")
        
        for criterion, score in result.scores.items():
            print(f"  {criterion}: {score} - {result.reasoning.get(criterion, 'No reasoning provided')}")
    
    # Calculate aggregate scores
    scores = evaluator.calculate_scores(evaluations)
    
    print("\n=== Overall Evaluation Results ===")
    print(f"Number of examples: {scores['count']}")
    print(f"Overall mean score: {scores['overall']['mean']:.2f}")
    
    print("\n=== Scores By Criterion ===")
    for criterion, metrics in scores.get('criteria', {}).items():
        print(f"{criterion.capitalize()}: {metrics['mean']:.2f} (std: {metrics['std']:.2f})")
    
    # Convert to dataframe and save results
    df = evaluator.to_dataframe(evaluations)
    os.makedirs('results', exist_ok=True)
    df.to_csv('results/evaluation_results.csv', index=False)
    print("\nResults saved to results/evaluation_results.csv")
    
    # Create score distribution plot
    fig = evaluator.plot_scores(evaluations)
    fig.savefig('results/score_distribution.png')
    print("Score distribution plot saved to results/score_distribution.png")
    
    # Save raw evaluation results as JSON
    with open('results/evaluations.json', 'w') as f:
        json.dump([eval.model_dump() for eval in evaluations], f, indent=2)
    print("Raw evaluation data saved to results/evaluations.json")

if __name__ == "__main__":
    main() 