"""
Dummy course outline generator for SSE bug testing.

This module provides a fake generator that emits the exact same SSE event
sequence as the real course outline generator, but without any LLM calls.
It uses hardcoded data and asyncio.sleep() to simulate realistic timing.

Purpose: Reproduce the "first-load content doesn't appear" SSE bug without
incurring LLM costs or waiting for real generation.

Toggle via config.py -> DebugConfig.USE_DUMMY_GRAPH = True
"""

import uuid
import asyncio
from typing import AsyncGenerator, Dict, List, Optional


# Hardcoded realistic course outline data
DUMMY_COURSE_OUTLINE = {
    "course_title": "Introduction to Machine Learning",
    "classes": [
        {
            "class_number": 1,
            "class_title": "Foundations of Machine Learning",
            "learning_objectives": [
                "Define machine learning and its key paradigms",
                "Distinguish between supervised, unsupervised, and reinforcement learning",
            ],
            "key_topics": [
                "What is Machine Learning?",
                "History and evolution of ML",
                "Types of learning: supervised, unsupervised, reinforcement",
            ],
            "activities_projects": [
                "Group discussion: Identify ML applications in daily life",
                "Quiz: Classify problems by learning type",
            ],
        },
        {
            "class_number": 2,
            "class_title": "Data Preprocessing and Feature Engineering",
            "learning_objectives": [
                "Apply data cleaning techniques to real-world datasets",
                "Perform feature scaling, encoding, and selection",
            ],
            "key_topics": [
                "Data quality and cleaning",
                "Feature scaling and normalization",
                "One-hot encoding and label encoding",
            ],
            "activities_projects": [
                "Hands-on lab: Clean and preprocess a messy CSV dataset",
                "Mini-project: Feature engineering on the Titanic dataset",
            ],
        },
        {
            "class_number": 3,
            "class_title": "Supervised Learning: Regression",
            "learning_objectives": [
                "Implement linear and polynomial regression models",
                "Evaluate regression models using MSE, RMSE, and R²",
            ],
            "key_topics": [
                "Linear regression theory",
                "Polynomial regression",
                "Regularization: Ridge and Lasso",
                "Model evaluation metrics",
            ],
            "activities_projects": [
                "Lab: Build a house price predictor with scikit-learn",
                "Exercise: Compare regularization techniques on sample data",
            ],
        },
        {
            "class_number": 4,
            "class_title": "Supervised Learning: Classification",
            "learning_objectives": [
                "Implement logistic regression and decision tree classifiers",
                "Interpret confusion matrices and classification reports",
            ],
            "key_topics": [
                "Logistic regression",
                "Decision trees and random forests",
                "Evaluation: precision, recall, F1-score",
                "ROC curves and AUC",
            ],
            "activities_projects": [
                "Lab: Spam email classifier",
                "Group project: Compare classifiers on a chosen dataset",
            ],
        },
        {
            "class_number": 5,
            "class_title": "Neural Networks and Deep Learning Basics",
            "learning_objectives": [
                "Explain the architecture of a feedforward neural network",
                "Train a simple neural network using a modern framework",
            ],
            "key_topics": [
                "Perceptrons and activation functions",
                "Backpropagation and gradient descent",
                "Introduction to PyTorch / TensorFlow",
            ],
            "activities_projects": [
                "Lab: Build a digit recognizer on MNIST with PyTorch",
                "Reflection essay: When to use deep learning vs. classical ML",
            ],
        },
    ],
}


async def run_dummy_course_outline_generator(
    message: str,
    topic: Optional[str] = None,
    number_of_classes: Optional[int] = None,
    thread_id: Optional[str] = None,
    file_contents: Optional[List[Dict[str, str]]] = None,
    language: Optional[str] = None,
) -> AsyncGenerator[Dict, None]:
    """
    Dummy generator that mimics the real course outline generator's SSE events.

    Emits the exact same event sequence:
      1. thread_id event
      2. progress: initializingConversation
      3. progress: ingestingDocuments
      4. progress: generatingCourseOutline
      5. progress: evaluatingOutline
      6. progress: structuringResponse
      7. complete event with full CourseOutline data

    Total time: ~2-3 seconds (vs 30-120s for real generation).
    """
    try:
        # Validate required parameters for first call (same as real generator)
        is_first_call = thread_id is None
        if is_first_call:
            if topic is None:
                raise ValueError("topic is required for the first call")
            if number_of_classes is None:
                raise ValueError("number_of_classes is required for the first call")
            if language is None:
                raise ValueError("language is required for the first call")
            thread_id = str(uuid.uuid4())

        # 1. Thread ID (immediate)
        yield {"type": "thread_id", "thread_id": thread_id}

        # 2. Progress: initializing
        await asyncio.sleep(0.2)
        yield {"type": "progress", "message_key": "overlay.initializingConversation"}

        # 3. Progress: ingesting documents
        await asyncio.sleep(0.3)
        yield {"type": "progress", "message_key": "overlay.ingestingDocuments"}

        # 4. Progress: generating
        await asyncio.sleep(0.5)
        yield {"type": "progress", "message_key": "overlay.generatingCourseOutline"}

        # 5. Progress: evaluating
        await asyncio.sleep(0.4)
        yield {"type": "progress", "message_key": "overlay.evaluatingOutline"}

        # 6. Progress: structuring
        await asyncio.sleep(0.3)
        yield {"type": "progress", "message_key": "overlay.structuringResponse"}

        # 7. Build the response - adapt to requested number_of_classes
        await asyncio.sleep(0.3)

        outline = dict(DUMMY_COURSE_OUTLINE)
        # If topic was provided, use it in the title
        if topic:
            outline["course_title"] = f"Introduction to {topic}"

        # Trim or repeat classes to match requested number
        if number_of_classes and number_of_classes > 0:
            classes = list(DUMMY_COURSE_OUTLINE["classes"])
            if number_of_classes < len(classes):
                classes = classes[:number_of_classes]
            elif number_of_classes > len(classes):
                # Duplicate last class with incremented numbers
                while len(classes) < number_of_classes:
                    extra = dict(classes[-1])
                    extra["class_number"] = len(classes) + 1
                    extra["class_title"] = f"Advanced Topics - Part {len(classes) - 4}"
                    classes.append(extra)
            outline["classes"] = classes

        # 8. Complete event
        yield {"type": "complete", "data": outline}

    except ValueError as e:
        yield {"type": "error", "message": str(e)}
    except Exception as e:
        yield {
            "type": "error",
            "message": f"Error in dummy generator: {str(e)}",
        }
