"""
Pydantic schemas for lesson plans metadata.

This module provides models to represent a complete lesson: LessonPlan,
LessonSection, and ActivityPlan. Each model captures structured information
about a class/session (e.g., class number and title, learning objectives,
an ordered lesson breakdown, activities, and homework). 

The schema includes json_schema_extra example data to aid documentation and
OpenAPI/JSON Schema generation.
"""


from typing import List
from pydantic import BaseModel, Field

class LessonSection(BaseModel):
    """
    Represents a structured part of the lesson (e.g., Introduction, Core Content, Application, Summary).
    """
    section_title: str = Field(..., description="Title of this part of the lesson, e.g. 'Introduction', 'Core Content — Thread-Based Concurrency', 'Application', 'Summary'")
    description: str = Field(..., description="Content-rich teaching guide: for core content sections, include precise definitions, principles, inline concrete examples, and discussion questions. Use scannable talking points — no full monologues or dense paragraphs. Must contain the actual professional/academic subject matter, not just structural scaffolding. Detailed enough to deliver the section without additional preparation.")


class ActivityPlan(BaseModel):
    """
    A focused task that reinforces the core content taught in the lesson.
    """
    name: str = Field(..., description="Name or title of the activity")
    objective: str = Field(..., description="What conceptual understanding this activity reinforces")
    instructions: str = Field(..., description="Clear instructions for students. Primarily individual work; optionally note a group variant. Include a concrete example or expected outcome. The task should test understanding of the core content.")


class LessonPlan(BaseModel):
    """
    Detailed instructional plan expanding on a CourseClass.
    """
    class_number: int = Field(..., description="Class number from the course outline", ge=1)
    class_title: str = Field(..., description="Title of the lesson")
    
    learning_objective: str = Field(..., description="Main learning goal of this lesson")
    
    key_points: List[str] = Field(
        ..., 
        description="The professional content backbone: each item is a substantive knowledge statement with a concrete example or illustration — not a vague label (2–10 items)",
        min_length=4,
        max_length=10
    )

    lesson_breakdown: List[LessonSection] = Field(
        ...,
        description="Content-focused flow of the lesson (e.g., Introduction, Core Content sections, Application/Discussion, Summary)",
        min_length=4,
        max_length=10
    )

    activities: List[ActivityPlan] = Field(
        default_factory=list,
        description="Focused tasks that reinforce the core content (1-2 recommended, primarily individual)",
        min_length=1,
        max_length=5
    )

    homework: str = Field(
        ...,
        description="Homework or follow-up work assigned to students"
    )

    extra_activities: str = Field(
        ...,
        description="Optional enrichment or bonus activities for early finishers or advanced learners"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "class_number": 5,
                "class_title": "Concurrency Models — Threads, Async, and the GIL",
                "learning_objective": "Students will understand the trade-offs between thread-based and async concurrency in Python, and be able to choose the appropriate model for I/O-bound vs CPU-bound workloads.",
                "key_points": [
                    "A thread is an OS-level execution unit sharing the process's memory space. Benefit: simple mental model for parallelism. Cost: race conditions when threads mutate shared state without synchronization.",
                    "The Global Interpreter Lock (GIL) in CPython allows only one thread to execute Python bytecode at a time. Consequence: threading does NOT speed up CPU-bound Python code — it only helps when threads spend time waiting (I/O).",
                    "Async/await uses cooperative multitasking on a single thread via an event loop. Advantage: no race conditions from shared mutable state, lower memory overhead. Limitation: all code in the chain must be async-aware.",
                    "Decision heuristic: I/O-bound + many concurrent tasks → asyncio; I/O-bound + simple logic → threading; CPU-bound → multiprocessing (bypasses GIL).",
                    "Common misconception: 'async is always faster than threads.' For small numbers of I/O tasks, threading can be simpler and equally fast. Async shines at scale (thousands of concurrent connections)."
                ],
                "lesson_breakdown": [
                    {
                        "section_title": "Introduction — Why Concurrency Matters",
                        "description": "Framing: modern applications handle many tasks at once — web servers process thousands of requests, data pipelines fetch from multiple APIs. Sequential execution wastes time waiting. Concrete scenario: a script downloading 100 web pages sequentially takes ~50s; with concurrency, under 5s. Ask: 'Where in your own projects have you had a program sitting idle, waiting?' State today's goal: understand two main concurrency models and when to use each."
                    },
                    {
                        "section_title": "Core Content — Thread-Based Concurrency",
                        "description": "Definition: a thread is a separate flow of execution within the same process; all threads share memory. Show threading example: threads = [Thread(target=fetch, args=(url,)) for url in urls]; start/join pattern. Key points: shared memory is the advantage (easy data sharing) and the danger (race conditions). Race condition demo: two threads incrementing counter=0 with 1000 increments each → result < 2000. Ask: 'If both threads see counter=5, what do they both write?' → 6, losing one increment. The GIL: CPython serializes bytecode execution, so threads don't help CPU-bound work."
                    },
                    {
                        "section_title": "Core Content — Async/Await and the Event Loop",
                        "description": "Definition: async uses a single thread with an event loop switching between tasks at await points. Show asyncio+aiohttp example: async def fetch(session, url) with await resp.read(); asyncio.gather for concurrency. Key distinctions: no OS threads created, coroutines ~1KB vs ~8MB/thread. The event loop is the scheduler — cooperative, not preemptive. Critical limitation: a blocking call (e.g., time.sleep() instead of await asyncio.sleep()) freezes the loop. Ask: 'What happens if one coroutine uses requests.get() instead of aiohttp?' → blocks the entire event loop. Subtle: async is concurrent, not parallel."
                    },
                    {
                        "section_title": "Core Content — Choosing the Right Model",
                        "description": "Comparison table: threading (I/O-bound, few tasks, ~8MB/thread, high shared-state risk) vs asyncio (I/O-bound, many tasks, ~1KB/coroutine, low risk) vs multiprocessing (CPU-bound, true parallelism, separate memory). Decision flow: CPU-bound? → multiprocessing. I/O-bound + dozens of tasks? → threading. I/O-bound + thousands? → asyncio. Real-world example: web scraper fetching 10,000 pages — asyncio handles efficiently; threading exhausts OS resources. Ask: 'A script runs 8 CPU-heavy model trainings — which model and why?' → multiprocessing."
                    },
                    {
                        "section_title": "Application — Concurrency Analysis",
                        "description": "Present scenario: an application fetches data from 5 APIs, processes results (CPU), writes to DB. Students analyze individually which parts suit which model. Then 2-3 students share reasoning. Instructor highlights: fetch = I/O-bound (async/threading), processing = CPU-bound (multiprocessing), DB writes = I/O-bound. Takeaway: real systems often combine models."
                    },
                    {
                        "section_title": "Summary",
                        "description": "Consolidate: (1) threading = OS-level, shared memory, GIL-limited; (2) async = event loop, cooperative, lightweight; (3) multiprocessing = true parallelism, separate memory. The GIL is the key Python-specific differentiator. Preview next session: synchronization primitives (locks, semaphores, queues)."
                    }
                ],
                "activities": [
                    {
                        "name": "Concurrency Model Decision Matrix",
                        "objective": "Apply the decision heuristic to realistic scenarios, reinforcing when to choose each concurrency model.",
                        "instructions": "Individual work (optionally discuss in pairs after). Given 5 scenarios, determine the concurrency model and justify: (1) Web server with 10,000 WebSocket connections → asyncio; (2) Script resizing 500 images → multiprocessing; (3) CLI downloading 5 files from S3 → threading; (4) Chat app with 50,000 users → asyncio; (5) ML pipeline training 4 models → multiprocessing. For each: state the model, reasoning, and one risk."
                    }
                ],
                "homework": "Read 'Python's GIL — A Story of Concurrency' (realpython.com). Answer: (1) Why does the GIL exist? (2) What operations release the GIL? (3) Will removing the GIL (PEP 703) change the trade-off? Write a 1-page analysis.",
                "extra_activities": "Implement both a threaded and an async URL fetcher for 20 pages. Measure wall-clock time. Write a short report: which was faster, why, and at what scale would the difference become significant?"
            }
        }
    }