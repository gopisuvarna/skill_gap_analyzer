from typing import List, Dict
from django.db.models import Q
from apps.recommendations.models import Course

TARGET = 8

_STATIC_COURSES: List[Dict] = [
    {"title": "Python for Everybody", "provider": "Coursera / University of Michigan",
     "url": "https://www.coursera.org/specializations/python",
     "skills_taught": ["Python", "python"]},
    {"title": "Automate the Boring Stuff with Python", "provider": "freeCodeCamp",
     "url": "https://automatetheboringstuff.com/",
     "skills_taught": ["Python", "python", "scripting"]},
    {"title": "JavaScript Algorithms and Data Structures", "provider": "freeCodeCamp",
     "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/",
     "skills_taught": ["JavaScript", "javascript", "js"]},
    {"title": "TypeScript Full Course", "provider": "Traversy Media / YouTube",
     "url": "https://www.youtube.com/watch?v=BCg4U1FzODs",
     "skills_taught": ["TypeScript", "typescript", "ts"]},
    {"title": "React – The Complete Guide", "provider": "Udemy",
     "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/",
     "skills_taught": ["React", "react", "react.js", "reactjs"]},
    {"title": "Next.js & React – The Complete Guide", "provider": "Udemy",
     "url": "https://www.udemy.com/course/nextjs-react-the-complete-guide/",
     "skills_taught": ["Next.js", "next.js", "nextjs", "React", "react"]},
    {"title": "Django for Beginners", "provider": "William S. Vincent",
     "url": "https://djangoforbeginners.com/",
     "skills_taught": ["Django", "django", "Python", "python"]},
    {"title": "FastAPI Full Course", "provider": "freeCodeCamp / YouTube",
     "url": "https://www.youtube.com/watch?v=0sOvCWFmrtA",
     "skills_taught": ["FastAPI", "fastapi", "Python", "python"]},
    {"title": "SQL for Data Science", "provider": "Coursera / UC Davis",
     "url": "https://www.coursera.org/learn/sql-for-data-science",
     "skills_taught": ["SQL", "sql", "PostgreSQL", "postgresql"]},
    {"title": "PostgreSQL Tutorial", "provider": "PostgreSQL official",
     "url": "https://www.postgresqltutorial.com/",
     "skills_taught": ["PostgreSQL", "postgresql", "SQL", "sql"]},
    {"title": "Machine Learning Specialization", "provider": "Coursera / Andrew Ng",
     "url": "https://www.coursera.org/specializations/machine-learning-introduction",
     "skills_taught": ["Machine Learning", "machine learning", "ML", "scikit-learn", "Python"]},
    {"title": "Deep Learning Specialization", "provider": "Coursera / deeplearning.ai",
     "url": "https://www.coursera.org/specializations/deep-learning",
     "skills_taught": ["Deep Learning", "deep learning", "TensorFlow", "tensorflow", "Neural Networks"]},
    {"title": "Practical Deep Learning for Coders", "provider": "fast.ai",
     "url": "https://course.fast.ai/",
     "skills_taught": ["Deep Learning", "PyTorch", "pytorch", "Python"]},
    {"title": "Data Science with Python", "provider": "Coursera / IBM",
     "url": "https://www.coursera.org/professional-certificates/ibm-data-science",
     "skills_taught": ["Data Science", "data science", "Python", "pandas", "NumPy", "numpy"]},
    {"title": "AWS Cloud Practitioner Essentials", "provider": "AWS Training",
     "url": "https://explore.skillbuilder.aws/learn/course/external/view/elearning/134/aws-cloud-practitioner-essentials",
     "skills_taught": ["AWS", "aws", "Cloud", "cloud"]},
    {"title": "Docker & Kubernetes – The Practical Guide", "provider": "Udemy",
     "url": "https://www.udemy.com/course/docker-kubernetes-the-practical-guide/",
     "skills_taught": ["Docker", "docker", "Kubernetes", "kubernetes", "DevOps", "devops"]},
    {"title": "Google Cloud Fundamentals", "provider": "Google Cloud Skills Boost",
     "url": "https://www.cloudskillsboost.google/paths/9",
     "skills_taught": ["GCP", "gcp", "Google Cloud", "Cloud", "cloud"]},
    {"title": "Java Programming Masterclass", "provider": "Udemy / Tim Buchalka",
     "url": "https://www.udemy.com/course/java-the-complete-java-developer-course/",
     "skills_taught": ["Java", "java"]},
    {"title": "Spring Boot Tutorial", "provider": "Amigoscode / YouTube",
     "url": "https://www.youtube.com/watch?v=9SGDpanrc8U",
     "skills_taught": ["Spring Boot", "spring boot", "Spring", "spring", "Java"]},
    {"title": "The Complete Node.js Developer Course", "provider": "Udemy / Andrew Mead",
     "url": "https://www.udemy.com/course/the-complete-nodejs-developer-course-2/",
     "skills_taught": ["Node.js", "node.js", "nodejs", "Express.js", "JavaScript"]},
    {"title": "Git & GitHub Crash Course", "provider": "freeCodeCamp / YouTube",
     "url": "https://www.youtube.com/watch?v=RGOj5yH7evk",
     "skills_taught": ["Git", "git", "GitHub", "github", "Version Control"]},
    {"title": "NLP with Hugging Face Transformers", "provider": "Hugging Face",
     "url": "https://huggingface.co/learn/nlp-course/",
     "skills_taught": ["NLP", "nlp", "Natural Language Processing", "transformers", "Hugging Face"]},
    {"title": "Kubernetes for Absolute Beginners", "provider": "KodeKloud / Udemy",
     "url": "https://www.udemy.com/course/learn-kubernetes/",
     "skills_taught": ["Kubernetes", "kubernetes", "k8s", "DevOps"]},
    {"title": "Linux Command Line Basics", "provider": "Udacity",
     "url": "https://www.udacity.com/course/linux-command-line-basics--ud595",
     "skills_taught": ["Linux", "linux", "Shell Scripting", "Bash", "bash"]},
    {"title": "Grokking the System Design Interview", "provider": "Educative",
     "url": "https://www.educative.io/courses/grokking-the-system-design-interview",
     "skills_taught": ["System Design", "system design", "Architecture", "Microservices"]},
]


def _match_static(skill_names: List[str]) -> List[Dict]:
    seen: set = set()
    results: List[Dict] = []
    for course in _STATIC_COURSES:
        if len(results) >= TARGET:
            break
        if course["title"] in seen:
            continue
        taught_lower = {t.lower() for t in course["skills_taught"]}
        matched = [s for s in skill_names if s.lower() in taught_lower]
        if matched:
            seen.add(course["title"])
            results.append({
                "id": None,
                "title": course["title"],
                "provider": course["provider"],
                "url": course["url"],
                "skills_taught": course["skills_taught"],
                "matched_skills": matched,
            })
    return results


def get_courses_for_skills(skill_names: List[str]) -> List[Dict]:
    """
    Return up to TARGET (8) courses for the given skill-gap skills.
    skills_taught is a JSONField — uses icontains for text search across all rows.
    Scores results so courses covering higher-priority skills come first.
    Falls back to static list if DB returns nothing.
    """
    if not skill_names:
        return []

    skill_lower_map = {s.lower(): s for s in skill_names}
    skill_priority = {s.lower(): len(skill_names) - i for i, s in enumerate(skill_names)}

    # Build OR filter — icontains works correctly on JSONField (searches the stored JSON text)
    q = Q()
    for skill in skill_names:
        q |= Q(skills_taught__icontains=skill)

    # Fetch large pool so scoring has enough candidates
    pool = list(Course.objects.filter(q).distinct()[: TARGET * 10])

    if not pool:
        return _match_static(skill_names)

    # Score and rank by how many high-priority skills each course covers
    scored: List[tuple] = []
    for c in pool:
        taught_lower = {str(t).lower() for t in (c.skills_taught or [])}
        matched = [skill_lower_map[s] for s in skill_lower_map if s in taught_lower]
        if not matched:
            # icontains may match substrings in JSON text — do a looser check
            taught_str = " ".join(str(t).lower() for t in (c.skills_taught or []))
            matched = [skill_lower_map[s] for s in skill_lower_map if s in taught_str]
        if not matched:
            continue
        score = sum(skill_priority.get(m.lower(), 0) for m in matched)
        scored.append((score, {
            "id": str(c.id),
            "title": c.title,
            "provider": c.provider,
            "url": c.url,
            "skills_taught": c.skills_taught,
            "matched_skills": matched,
        }))

    scored.sort(key=lambda x: x[0], reverse=True)
    db_results = [item for _, item in scored]

    if db_results:
        return db_results[:TARGET]

    return _match_static(skill_names)