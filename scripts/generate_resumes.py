"""
Generate the 57 synthetic resumes that take the corpus from Milestone 2's 43 to 100.

Every person below is fictional, and so is every employer. Each person is written out by
hand as a career: a list of roles, oldest first, each with how long it lasted and the
stack used in it. Only the wording of the bullet points comes from templates. Writing the
careers by hand is what lets the corpus contain deliberate traps for the agent, such as a
React Native developer who never used React for the web, or someone who switched to React
a year ago after five years of Angular. DATASET.md lists every trap.

The output is deterministic: running the script twice writes byte-identical .md, .txt and
.pdf files. A .docx is a zip archive whose entry timestamps change between runs, so only
its text is reproducible.

Usage
  python scripts/generate_resumes.py            # writes into resumes/
  python scripts/generate_resumes.py --out tmp/ # somewhere else
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

AS_OF = (2026, 10)  # the "Present" every open-ended role runs to
FIXED_DATE = datetime(2026, 10, 31)
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "resumes"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


# --------------------------------------------------------------------------- #
# Role families: job titles by seniority, default degree, and bullet templates.
# In a template {a} is the first item of the role's stack, {b} the second, and so on.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Family:
    noun: str                              # "frontend engineer", used in the summary
    titles: tuple[str, str, str, str]      # junior, mid, senior, staff
    degree: str
    bullets: tuple[str, ...]


FAMILIES = {
    "frontend": Family(
        "frontend engineer",
        ("Junior Frontend Developer", "Frontend Engineer", "Senior Frontend Engineer", "Staff Frontend Engineer"),
        "B.Sc. in Computer Science",
        ("Built and maintained {a} components in {b} for a customer-facing web app with {n}k monthly users.",
         "Led the migration of legacy pages to {a}, cutting the JavaScript bundle by {p}%.",
         "Introduced {c} and {d} into the team's workflow and wrote the conventions guide.",
         "Worked with designers in Figma to ship an accessible (WCAG 2.1 AA) component library in {a}.",
         "Improved Core Web Vitals on the checkout flow, reducing LCP by {p}% with code splitting.",
         "Reviewed {a} pull requests for a team of {k} engineers and ran a weekly frontend guild.")),
    "fullstack": Family(
        "full-stack engineer",
        ("Junior Software Developer", "Full-Stack Developer", "Senior Full-Stack Engineer", "Lead Full-Stack Engineer"),
        "B.Sc. in Computer Science",
        ("Shipped end-to-end features with {a} and {b}, from database schema to UI.",
         "Designed REST APIs consumed by web and mobile clients serving {n}k users.",
         "Moved the team's deployment to {c} and {d}, cutting release time from days to hours.",
         "Built an internal admin dashboard with {a} used daily by {k} operations staff.",
         "Owned on-call for the {b} services and reduced paging alerts by {p}%.")),
    "backend": Family(
        "backend engineer",
        ("Junior Backend Developer", "Backend Engineer", "Senior Backend Engineer", "Principal Backend Engineer"),
        "B.Sc. in Computer Engineering",
        ("Built and operated {a} services handling {n}k requests per minute at peak.",
         "Designed the {c} data model for the payments ledger and wrote its migration plan.",
         "Introduced {d} for the team's services and documented the runbooks.",
         "Cut p99 latency of the orders API by {p}% by reworking queries and caching.",
         "Mentored {k} engineers and led design reviews for new {b} services.")),
    "mobile": Family(
        "mobile engineer",
        ("Junior Mobile Developer", "Mobile Engineer", "Senior Mobile Engineer", "Lead Mobile Engineer"),
        "B.Sc. in Computer Science",
        ("Built the {a} app used by {n}k monthly active users, rated {r} in the store.",
         "Rewrote the onboarding flow in {b}, lifting completion by {p}%.",
         "Set up {c} and {d} for the mobile team and automated store releases.",
         "Reduced app start-up time by {p}% through lazy loading and image caching.",
         "Paired with backend engineers to design offline-first sync for {a}.")),
    "ml": Family(
        "machine learning engineer",
        ("Junior ML Engineer", "Machine Learning Engineer", "Senior Machine Learning Engineer", "Staff ML Engineer"),
        "M.Sc. in Machine Learning",
        ("Trained and deployed {a} models serving {n}k predictions a day.",
         "Built a {b} pipeline that cut model iteration time from weeks to days.",
         "Productionised models with {c} and {d}, with offline and online evaluation.",
         "Improved ranking quality (nDCG@10) by {p}% with a retrained {a} model.",
         "Mentored {k} engineers on experiment design and model evaluation.")),
    "data_eng": Family(
        "data engineer",
        ("Junior Data Engineer", "Data Engineer", "Senior Data Engineer", "Lead Data Engineer"),
        "B.Sc. in Information Systems",
        ("Built batch and streaming pipelines with {a} and {b} processing {n} GB a day.",
         "Modelled the analytics warehouse in {c}, replacing {k} ad-hoc reporting databases.",
         "Introduced data quality checks and orchestration with {d}.",
         "Cut pipeline cost by {p}% by repartitioning tables and pruning unused jobs.",
         "Worked with analysts to define core metrics and their {a} lineage.")),
    "devops": Family(
        "DevOps engineer",
        ("Junior DevOps Engineer", "DevOps Engineer", "Senior Site Reliability Engineer", "Staff Site Reliability Engineer"),
        "B.Sc. in Computer Networks",
        ("Ran production infrastructure on {a} and {b} for {k} product teams.",
         "Codified environments with {c}, replacing hand-built servers.",
         "Built CI/CD pipelines with {d} that cut deployment time by {p}%.",
         "Led incident response and wrote postmortems; raised availability to 99.9{r}%.",
         "Introduced SLOs and alerting that reduced pages per week by {p}%.")),
    "data_sci": Family(
        "data scientist",
        ("Junior Data Analyst", "Data Scientist", "Senior Data Scientist", "Lead Data Scientist"),
        "M.Sc. in Statistics",
        ("Analysed product funnels with {a} and {b} and presented findings to leadership.",
         "Designed and evaluated A/B tests for pricing changes affecting {n}k customers.",
         "Built churn and lifetime-value models in {a}, adopted by the growth team.",
         "Created self-serve dashboards in {d} used weekly by {k} managers.",
         "Automated monthly reporting with {c}, saving {k} analyst-days a month.")),
    "qa": Family(
        "QA automation engineer",
        ("QA Analyst", "QA Automation Engineer", "Senior QA Automation Engineer", "QA Lead"),
        "B.Sc. in Software Engineering",
        ("Built an end-to-end test suite with {a} and {b} covering {n} critical user journeys.",
         "Cut flaky tests by {p}% by rewriting waits and isolating test data.",
         "Ran the test suite in {d} on every pull request, blocking regressions before release.",
         "Introduced {c} for API contract testing between {k} services.")),
    "security": Family(
        "application security engineer",
        ("Security Analyst", "Application Security Engineer", "Senior Application Security Engineer", "Security Lead"),
        "B.Sc. in Computer Science",
        ("Ran threat modelling and design reviews for {k} product teams.",
         "Triaged findings from {b} and the bug bounty programme; fixed {n} high-severity issues.",
         "Built secure-by-default service templates with {c} and {d}.",
         "Taught secure coding workshops covering the OWASP Top 10 to {n} engineers.")),
    "manager": Family(
        "engineering manager",
        ("Team Lead", "Engineering Manager", "Senior Engineering Manager", "Director of Engineering"),
        "B.Sc. in Computer Science",
        ("Managed a team of {k} engineers across web and mobile; hired {k} engineers.",
         "Ran quarterly planning and the delivery roadmap with product and design.",
         "Introduced career ladders and a weekly on-call review.",
         "Cut cycle time by {p}% by splitting the release train and adding feature flags.")),
    "designer": Family(
        "product designer",
        ("Junior Product Designer", "Product Designer", "Senior Product Designer", "Lead Product Designer"),
        "B.A. in Interaction Design",
        ("Designed end-to-end flows in {a} for a product with {n}k monthly users.",
         "Ran {k} rounds of user research and usability testing per quarter.",
         "Built and documented the {b} and its accessibility guidelines.",
         "Worked with engineers to ship the design system, using {c} and {d}.")),
}


# --------------------------------------------------------------------------- #
# People
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Role:
    years: float
    stack: tuple[str, ...]
    family: str | None = None   # defaults to the person's family
    title: str | None = None    # defaults to a title chosen by seniority
    gap_note: str | None = None  # set for a career break instead of a job


@dataclass(frozen=True)
class Person:
    slug: str
    name: str
    city: str
    family: str
    fmt: str                        # md, txt, docx or pdf
    roles: tuple[Role, ...]         # oldest first
    summary: str | None = None      # defaults to a summary built from the roles
    extra_skills: tuple[str, ...] = ()
    education: tuple[str, ...] | None = None
    extras: tuple[tuple[str, tuple[str, ...]], ...] = ()  # extra sections such as Projects


def R(years: float, *stack: str, family: str | None = None, title: str | None = None) -> Role:
    return Role(years, tuple(stack), family, title)


def GAP(years: float, note: str) -> Role:
    return Role(years, (), gap_note=note)


PEOPLE: tuple[Person, ...] = (
    # Frontend
    Person("grace_liu", "Grace Liu", "Singapore", "frontend", "md",
           (R(3.0, "React", "JavaScript", "Redux", "Sass"), R(5.2, "React", "TypeScript", "Storybook", "Figma")),
           summary="Frontend engineer with 8 years of React who leads a design system used by six product teams."),
    Person("ethan_walsh", "Ethan Walsh", "Dublin, Ireland", "frontend", "txt",
           (R(2.0, "Vue", "JavaScript", "Vuex", "Jest"), R(3.4, "React", "TypeScript", "Next.js", "Playwright"))),
    Person("camila_reyes", "Camila Reyes", "Bogotá, Colombia", "frontend", "md",
           (R(4.1, "React", "TypeScript", "Next.js", "GraphQL"),)),
    Person("chloe_martin", "Chloe Martin", "Lyon, France", "frontend", "md",
           (R(4.5, "Angular", "TypeScript", "RxJS", "Sass"), R(1.2, "React", "TypeScript", "Redux", "Jest")),
           summary="Frontend engineer with 5 years of experience, now building React and TypeScript apps."),
    Person("elif_yildiz", "Elif Yildiz", "Istanbul, Turkey", "frontend", "txt",
           (R(2.5, "Vue", "JavaScript", "Vuex", "Sass"), R(2.8, "Vue", "TypeScript", "Nuxt", "Vitest"))),
    Person("jonas_weber", "Jonas Weber", "Berlin, Germany", "frontend", "md",
           (R(1.5, "React", "JavaScript", "Webpack", "Jest"), R(2.7, "Svelte", "TypeScript", "SvelteKit", "Vite"))),
    Person("aaliyah_johnson", "Aaliyah Johnson", "Atlanta, GA", "frontend", "txt",
           (R(1.1, "React", "JavaScript", "HTML/CSS", "Jest"),),
           education=("Full-Stack Web Development Certificate, Peachtree Coding Bootcamp, 2025",
                      "B.A. in Psychology, Georgia State University, 2023")),
    Person("hana_sato", "Hana Sato", "Tokyo, Japan", "frontend", "md",
           (R(2.2, "React", "JavaScript", "Redux", "Sass"), R(4.3, "React", "TypeScript", "React Query", "Playwright"))),
    Person("lucas_moreau", "Lucas Moreau", "Paris, France", "frontend", "docx",
           (R(3.0, "Angular", "TypeScript", "RxJS", "NgRx"), R(3.5, "Angular", "TypeScript", "Nx", "Jest"))),
    Person("patrick_oneill", "Patrick O'Neill", "Cork, Ireland", "frontend", "txt",
           (R(2.1, "PHP", "WordPress", "jQuery", "React", title="Web Developer"),),
           summary="Full-stack developer experienced in React, Vue, Angular, Node.js, Python, Kubernetes, "
                   "AWS and machine learning with TensorFlow.",
           extra_skills=("Vue", "Angular", "Node.js", "Python", "Kubernetes", "AWS", "TensorFlow", "Docker", "GraphQL")),
    # Full-stack
    Person("mia_schneider", "Mia Schneider", "Munich, Germany", "fullstack", "md",
           (R(2.5, "Node.js", "JavaScript", "Express", "MongoDB"), R(3.8, "React", "Node.js", "TypeScript", "PostgreSQL"))),
    Person("rohan_desai", "Rohan Desai", "Bengaluru, India", "fullstack", "txt",
           (R(3.0, "Django", "Python", "PostgreSQL", "jQuery"), R(2.6, "React", "Django", "TypeScript", "Docker"))),
    Person("william_turner", "William Turner", "Seattle, WA", "fullstack", "md",
           (R(4.0, "Ruby on Rails", "Ruby", "PostgreSQL", "Sidekiq"),
            R(5.3, "React", "TypeScript", "Ruby on Rails", "GraphQL"))),
    Person("gabriel_costa", "Gabriel Costa", "Rio de Janeiro, Brazil", "fullstack", "txt",
           (R(3.3, "Node.js", "TypeScript", "NestJS", "PostgreSQL"), R(2.0, "Next.js", "React", "TypeScript", "Prisma"))),
    Person("tomasz_kowalski", "Tomasz Kowalski", "Warsaw, Poland", "backend", "md",
           (R(3.0, "Java", "Spring Boot", "MySQL", "Jenkins"), R(4.2, "Java", "Spring Boot", "Kafka", "Kubernetes")),
           extras=(("Side Projects", ("Built a personal budgeting web app with React and Firebase as a weekend project (2024).",)),)),
    Person("noah_fischer", "Noah Fischer", "Zurich, Switzerland", "fullstack", "docx",
           (R(2.8, "Vue", "Laravel", "PHP", "MySQL"), R(3.1, "React", "Node.js", "TypeScript", "AWS"))),
    # Backend
    Person("natalia_popescu", "Natalia Popescu", "Bucharest, Romania", "backend", "txt",
           (R(4.0, "Java", "Spring Boot", "PostgreSQL", "Docker"),
            GAP(1.75, "Career break for family caregiving."),
            R(2.2, "Java", "Spring Boot", "Kafka", "Kubernetes"))),
    Person("pablo_ruiz", "Pablo Ruiz", "Madrid, Spain", "backend", "md",
           (R(3.0, "Python", "Django", "PostgreSQL", "Celery"), R(4.5, "Go", "gRPC", "PostgreSQL", "Kubernetes"))),
    Person("oscar_mendes", "Oscar Mendes", "Lisbon, Portugal", "backend", "md",
           (R(2.5, "Ruby", "Ruby on Rails", "PostgreSQL", "Redis"), R(4.0, "Elixir", "Phoenix", "PostgreSQL", "RabbitMQ"))),
    Person("farhan_chowdhury", "Farhan Chowdhury", "Dhaka, Bangladesh", "backend", "txt",
           (R(2.0, "PHP", "Laravel", "MySQL", "Redis"), R(3.6, "Node.js", "TypeScript", "PostgreSQL", "AWS"))),
    Person("ingrid_halvorsen", "Ingrid Halvorsen", "Oslo, Norway", "backend", "md",
           (R(5.0, "C#", ".NET", "SQL Server", "Azure"), R(4.2, "C#", ".NET", "Microservices", "Kubernetes"))),
    Person("vivek_menon", "Vivek Menon", "Kochi, India", "backend", "txt",
           (R(3.5, "Java", "Spring Boot", "Oracle", "Jenkins"), R(3.4, "Kotlin", "Spring Boot", "Kafka", "AWS"))),
    Person("clara_jensen", "Clara Jensen", "Copenhagen, Denmark", "backend", "pdf",
           (R(2.6, "Python", "Flask", "PostgreSQL", "Docker"), R(3.0, "Python", "FastAPI", "Redis", "AWS"))),
    Person("ahmed_karim", "Ahmed Karim", "Dubai, UAE", "backend", "md",
           (R(4.0, "Go", "PostgreSQL", "Redis", "Docker"), R(6.1, "Go", "Kafka", "Kubernetes", "System Design"))),
    # Mobile
    Person("kenji_watanabe", "Kenji Watanabe", "Osaka, Japan", "mobile", "md",
           (R(2.4, "React Native", "JavaScript", "Redux", "Firebase"), R(3.1, "React Native", "TypeScript", "Expo", "iOS"))),
    Person("minh_nguyen", "Minh Nguyen", "Ho Chi Minh City, Vietnam", "mobile", "txt",
           (R(4.6, "React Native", "TypeScript", "GraphQL", "Android"),)),
    Person("sneha_kulkarni", "Sneha Kulkarni", "Mumbai, India", "mobile", "md",
           (R(3.0, "Android", "Kotlin", "Jetpack Compose", "Firebase"), R(3.2, "Android", "Kotlin", "Coroutines", "CI/CD"))),
    Person("haruto_kimura", "Haruto Kimura", "Fukuoka, Japan", "mobile", "txt",
           (R(2.5, "iOS", "Swift", "UIKit", "Core Data"), R(4.0, "iOS", "Swift", "SwiftUI", "Combine"))),
    Person("laura_bianchi", "Laura Bianchi", "Milan, Italy", "mobile", "docx",
           (R(3.0, "Flutter", "Dart", "Firebase", "Android"), R(2.4, "Swift", "iOS", "SwiftUI", "Kotlin"))),
    # Machine learning
    Person("adaeze_nwosu", "Adaeze Nwosu", "Lagos, Nigeria", "ml", "md",
           (R(2.5, "Python", "scikit-learn", "Pandas", "SQL"), R(4.0, "PyTorch", "LLMs", "RAG", "AWS"))),
    Person("ishaan_kapoor", "Ishaan Kapoor", "Pune, India", "ml", "txt",
           (R(3.0, "TensorFlow", "Python", "Computer Vision", "Docker"), R(3.3, "PyTorch", "Computer Vision", "MLOps", "GCP"))),
    Person("leila_ahmadi", "Leila Ahmadi", "Vancouver, Canada", "ml", "md",
           (R(4.4, "PyTorch", "NLP", "Hugging Face", "LangChain"),),
           education=("PhD in Computer Science (NLP), University of British Columbia, 2022",
                      "B.Sc. in Computer Engineering, Sharif University of Technology, 2016")),
    Person("tariq_mahmood", "Tariq Mahmood", "Karachi, Pakistan", "ml", "txt",
           (R(2.0, "Python", "Pandas", "scikit-learn", "Flask"), R(2.8, "PyTorch", "LLMs", "Vector Databases", "FastAPI"))),
    Person("hyunwoo_choi", "Hyun-woo Choi", "Seoul, South Korea", "ml", "pdf",
           (R(3.5, "C++", "CUDA", "PyTorch", "Computer Vision"), R(3.0, "PyTorch", "Deep Learning", "Kubernetes", "MLOps"))),
    Person("meera_pillai", "Meera Pillai", "Chennai, India", "ml", "md",
           (R(5.5, "Python", "Spark", "MLOps", "AWS"), R(3.0, "LLMs", "RAG", "PyTorch", "Kubernetes"))),
    # Data engineering
    Person("lars_johansson", "Lars Johansson", "Gothenburg, Sweden", "data_eng", "md",
           (R(3.0, "SQL", "Python", "Redshift", "Airflow"), R(3.5, "Spark", "Kafka", "AWS", "Airflow"))),
    Person("thandiwe_dlamini", "Thandiwe Dlamini", "Johannesburg, South Africa", "data_eng", "txt",
           (R(2.2, "SQL", "Python", "Snowflake", "dbt"), R(2.6, "dbt", "Kafka", "Snowflake", "Airflow"))),
    Person("jakub_novotny", "Jakub Novotny", "Prague, Czech Republic", "data_eng", "md",
           (R(4.0, "Scala", "Spark", "Hadoop", "Hive"), R(3.2, "Spark", "Kafka", "Flink", "GCP"))),
    Person("amina_diallo", "Amina Diallo", "Dakar, Senegal", "data_eng", "txt",
           (R(3.1, "Python", "SQL", "BigQuery", "Airflow"),)),
    Person("kofi_asante", "Kofi Asante", "Kumasi, Ghana", "data_eng", "md",
           (R(2.5, "Python", "Pandas", "SQL", "Excel", title="Data Analyst"), R(2.0, "Python", "Spark", "Databricks", "Azure"))),
    # DevOps and SRE
    Person("samuel_osei", "Samuel Osei", "Accra, Ghana", "devops", "md",
           (R(3.0, "Linux", "AWS", "Bash", "Jenkins"), R(4.3, "Kubernetes", "AWS", "Terraform", "Prometheus"))),
    Person("zainab_yusuf", "Zainab Yusuf", "Abuja, Nigeria", "devops", "txt",
           (R(2.8, "Linux", "Docker", "GCP", "GitLab CI"), R(3.0, "Kubernetes", "GCP", "Terraform", "Go"))),
    Person("felix_wagner", "Felix Wagner", "Vienna, Austria", "devops", "docx",
           (R(5.0, "Linux", "VMware", "Ansible", "Bash"), R(4.6, "Kubernetes", "Azure", "Terraform", "CI/CD"))),
    Person("rania_saleh", "Rania Saleh", "Cairo, Egypt", "devops", "md",
           (R(3.4, "AWS", "Docker", "Terraform", "Python"),)),
    Person("andile_khumalo", "Andile Khumalo", "Cape Town, South Africa", "devops", "txt",
           (R(2.2, "Linux", "Docker", "Bash", "Jenkins"), R(2.9, "Kubernetes", "AWS", "Helm", "Prometheus"))),
    Person("divya_reddy", "Divya Reddy", "Hyderabad, India", "devops", "md",
           (R(4.0, "Linux", "Python", "Docker", "Jenkins"), R(3.7, "Kubernetes", "AWS", "Terraform", "System Design"))),
    # Data science
    Person("anika_bose", "Anika Bose", "Kolkata, India", "data_sci", "md",
           (R(3.2, "Python", "SQL", "Statistics", "Tableau"), R(2.5, "Python", "scikit-learn", "dbt", "Tableau"))),
    Person("olivia_bennett", "Olivia Bennett", "Manchester, UK", "data_sci", "txt",
           (R(2.0, "R", "SQL", "Excel", "Statistics"), R(3.4, "Python", "SQL", "Statistics", "Looker"))),
    Person("nadia_benali", "Nadia Benali", "Casablanca, Morocco", "data_sci", "md",
           (R(4.8, "Python", "Pandas", "scikit-learn", "SQL"),)),
    Person("ricardo_alves", "Ricardo Alves", "Porto, Portugal", "data_sci", "txt",
           (R(3.0, "Excel", "SQL", "Statistics", "Power BI", title="Data Analyst"),
            R(2.6, "Python", "SQL", "Statistics", "Tableau"))),
    Person("esther_mwangi", "Esther Mwangi", "Nairobi, Kenya", "data_sci", "pdf",
           (R(2.7, "Python", "R", "Statistics", "SQL"), R(3.0, "Python", "PyTorch", "BigQuery", "Statistics"))),
    # QA, security, management and design
    Person("yara_nasser", "Yara Nasser", "Amman, Jordan", "qa", "md",
           (R(3.1, "Selenium", "Java", "TestNG", "Jenkins"), R(2.6, "Playwright", "TypeScript", "Pact", "GitHub Actions"))),
    Person("siddharth_iyengar", "Siddharth Iyengar", "Mysuru, India", "qa", "md",
           (R(4.2, "Selenium", "Python", "Pytest", "Jenkins"),)),
    Person("ayesha_siddiqui", "Ayesha Siddiqui", "Lahore, Pakistan", "qa", "txt",
           (R(2.3, "Cypress", "JavaScript", "React Testing Library", "GitHub Actions"),)),
    Person("mateo_silva", "Mateo Silva", "São Paulo, Brazil", "security", "md",
           (R(3.0, "Python", "Burp Suite", "OWASP ZAP", "AWS"), R(3.4, "Go", "Semgrep", "Kubernetes", "Terraform"))),
    Person("benjamin_carter", "Benjamin Carter", "Austin, TX", "frontend", "md",
           (R(1.5, "JavaScript", "jQuery", "Backbone.js", "HTML/CSS"),
            R(6.5, "React", "TypeScript", "Redux", "Node.js"),
            R(3.2, "Agile", "Leadership", "Hiring", "Roadmapping", family="manager", title="Engineering Manager")),
           summary="Engineering manager with 11 years in web development, the last 3 leading a team of eight "
                   "instead of writing production code."),
    Person("sophie_laurent", "Sophie Laurent", "Brussels, Belgium", "designer", "docx",
           (R(3.0, "Figma", "Sketch", "User Research", "Prototyping"),
            R(3.5, "Figma", "Design Systems", "HTML/CSS", "Accessibility"))),
)

COMPANIES = (
    "Brightloop", "Quillstone", "Harborview Analytics", "Tidewell", "Ferncastle", "Lumenfield",
    "Copperleaf Systems", "Stratawave", "Bluefinch", "Meridian Freight", "Kestrel Pay", "Juniper Retail Cloud",
    "Pinecrest Media", "Orbitly", "Vantage Learning", "Solace Bank", "Greystone Logistics", "Cinder Games",
    "Arclight Mobility", "Willow Insurance", "Hollowbrook Health", "Nimbusly", "Saffron Commerce",
    "Trellis Health", "Ironbark Security", "Lattice Robotics", "Ember Analytics", "Northgate Travel",
    "Silverpine Energy", "Coral Telecom",
)


# --------------------------------------------------------------------------- #
# From a Person to resume text
# --------------------------------------------------------------------------- #
@dataclass
class Job:
    heading: str      # "Senior Frontend Engineer, Brightloop"
    dates: str        # "Mar 2021 - Present"
    bullets: list[str] = field(default_factory=list)


@dataclass
class Resume:
    name: str
    contact: str
    summary: str
    skills: list[str]
    jobs: list[Job]
    education: list[str]
    extras: list[tuple[str, list[str]]]


def _month_index(year: int, month: int) -> int:
    return year * 12 + (month - 1)


def _fmt_month(index: int) -> str:
    return f"{MONTHS[index % 12]} {index // 12}"


def _seniority(years_in: float) -> int:
    """Title level for someone `years_in` years into their career."""
    if years_in < 1.5:
        return 0
    if years_in < 4:
        return 1
    if years_in < 8:
        return 2
    return 3


def _bullets(family: Family, stack: tuple[str, ...], rng: random.Random, count: int) -> list[str]:
    padded = list(stack) + [stack[0]] * (4 - len(stack))
    values = dict(zip("abcd", padded), n=rng.choice((40, 75, 120, 250, 600)), p=rng.choice((18, 25, 30, 35, 40, 55)),
                  k=rng.choice((3, 4, 5, 6, 8)), r=rng.choice((4.6, 4.7, 4.8)))
    return [t.format(**values) for t in rng.sample(family.bullets, k=min(count, len(family.bullets)))]


def build_resume(person: Person) -> Resume:
    rng = random.Random(person.slug)  # per-person seed: adding a person never changes the others
    family = FAMILIES[person.family]
    companies = rng.sample(COMPANIES, k=len(person.roles))

    # Lay the roles out backwards from AS_OF so the most recent one ends "Present".
    end = _month_index(*AS_OF)
    spans = []
    for role in reversed(person.roles):
        months = round(role.years * 12)
        spans.append((role, end - months + 1, end))
        end -= months
    spans.reverse()

    jobs, years_so_far, total_years = [], 0.0, 0.0
    for i, (role, start, stop) in enumerate(spans):
        if role.gap_note:
            jobs.append(Job("Career break", f"{_fmt_month(start)} - {_fmt_month(stop)}", [role.gap_note]))
            continue
        role_family = FAMILIES[role.family or person.family]
        # Title by seniority half-way through the role, so a 4-year first job isn't "Junior".
        title = role.title or role_family.titles[_seniority(years_so_far + role.years / 2)]
        is_last = i == len(spans) - 1
        dates = f"{_fmt_month(start)} - {'Present' if is_last else _fmt_month(stop)}"
        jobs.append(Job(f"{title}, {companies[i]}", dates, _bullets(role_family, role.stack, rng, 3 if is_last else 2)))
        years_so_far += role.years
        total_years += role.years
    jobs.reverse()  # resumes list the most recent role first

    skills: list[str] = []
    for role in person.roles:
        skills += [s for s in role.stack if s not in skills]
    skills += [s for s in person.extra_skills if s not in skills]

    latest = next(r for r in reversed(person.roles) if not r.gap_note)
    summary = person.summary or (
        # int() rounds down: a summary must never claim more years than the roles add up to.
        f"{family.noun[0].upper()}{family.noun[1:]} with {int(total_years)} years of experience, "
        f"most recently working with {', '.join(latest.stack[:3])}.")
    first_year = spans[0][1] // 12
    city = person.city.split(",")[0]
    education = list(person.education or (f"{family.degree}, University of {city}, {first_year}",))
    email = person.name.lower().replace("'", "").replace("-", "").replace(" ", ".") + "@example.com"
    return Resume(person.name, f"{email} | {person.city}", summary, skills, jobs, education,
                  [(heading, list(lines)) for heading, lines in person.extras])


# --------------------------------------------------------------------------- #
# Writers
# --------------------------------------------------------------------------- #
def render_markdown(r: Resume) -> str:
    lines = [f"# {r.name}", r.contact, "", "## Summary", r.summary, "", "## Skills", ", ".join(r.skills), "",
             "## Experience"]
    for job in r.jobs:
        lines += [job.heading, job.dates, *[f"- {b}" for b in job.bullets], ""]
    lines += ["## Education", *r.education]
    for heading, extra in r.extras:
        lines += ["", f"## {heading}", *[f"- {line}" for line in extra]]
    return "\n".join(lines) + "\n"


def render_text(r: Resume) -> str:
    lines = [f"Name: {r.name}", r.contact, "", "SUMMARY", r.summary, "", "SKILLS", ", ".join(r.skills), "",
             "EXPERIENCE"]
    for job in r.jobs:
        lines += [job.heading, job.dates, *[f"- {b}" for b in job.bullets], ""]
    lines += ["EDUCATION", *r.education]
    for heading, extra in r.extras:
        lines += ["", heading.upper(), *[f"- {line}" for line in extra]]
    return "\n".join(lines) + "\n"


def write_docx(r: Resume, path: Path) -> None:
    import docx  # noqa: PLC0415  (only the .docx writer needs python-docx)

    document = docx.Document()
    props = document.core_properties
    props.author, props.title = r.name, f"{r.name} - Resume"
    props.created = props.modified = FIXED_DATE
    document.add_heading(r.name, level=0)
    document.add_paragraph(r.contact)
    for heading, text in (("Summary", r.summary), ("Skills", ", ".join(r.skills))):
        document.add_heading(heading, level=1)
        document.add_paragraph(text)
    document.add_heading("Experience", level=1)
    for job in r.jobs:
        document.add_paragraph().add_run(job.heading).bold = True
        document.add_paragraph(job.dates)
        for bullet in job.bullets:
            document.add_paragraph(bullet, style="List Bullet")
    document.add_heading("Education", level=1)
    for line in r.education:
        document.add_paragraph(line)
    for heading, extra in r.extras:
        document.add_heading(heading, level=1)
        for line in extra:
            document.add_paragraph(line, style="List Bullet")
    document.save(str(path))


def write_pdf(r: Resume, path: Path) -> None:
    from reportlab import rl_config  # noqa: PLC0415  (only the .pdf writer needs reportlab)
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate

    rl_config.invariant = 1  # fixed creation date and document id, so the bytes are reproducible
    styles = getSampleStyleSheet()
    body, h2 = styles["BodyText"], styles["Heading2"]
    story = [Paragraph(escape(r.name), styles["Title"]), Paragraph(escape(r.contact), body),
             Paragraph("Summary", h2), Paragraph(escape(r.summary), body),
             Paragraph("Skills", h2), Paragraph(escape(", ".join(r.skills)), body),
             Paragraph("Experience", h2)]
    for job in r.jobs:
        story += [Paragraph(f"<b>{escape(job.heading)}</b>", body), Paragraph(escape(job.dates), body)]
        story += [Paragraph(f"- {escape(b)}", body) for b in job.bullets]
    story.append(Paragraph("Education", h2))
    story += [Paragraph(escape(line), body) for line in r.education]
    for heading, extra in r.extras:
        story.append(Paragraph(escape(heading), h2))
        story += [Paragraph(f"- {escape(line)}", body) for line in extra]
    SimpleDocTemplate(str(path), pagesize=A4, title=f"{r.name} - Resume", author=r.name).build(story)


def write(person: Person, out_dir: Path) -> Path:
    resume = build_resume(person)
    path = out_dir / f"{person.slug}.{person.fmt}"
    if person.fmt == "md":
        path.write_text(render_markdown(resume), encoding="utf-8")
    elif person.fmt == "txt":
        path.write_text(render_text(resume), encoding="utf-8")
    elif person.fmt == "docx":
        write_docx(resume, path)
    elif person.fmt == "pdf":
        write_pdf(resume, path)
    else:
        raise ValueError(f"unknown format {person.fmt!r} for {person.slug}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the 57 synthetic resumes added in Milestone 3.")
    parser.add_argument("--out", type=Path, default=OUTPUT_DIR, help="Directory to write the resumes into")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    # A generated slug must never shadow another resume: re-running overwrites this
    # script's own files, but a same-named file in another format belongs to someone else.
    existing = list(args.out.iterdir())
    clashes = sorted(person.slug for person in PEOPLE
                     if any(f.stem == person.slug and f.suffix != f".{person.fmt}" for f in existing))
    if clashes:
        raise SystemExit(f"refusing to write: these names are already used by other resumes: {clashes}")
    for person in PEOPLE:
        write(person, args.out)
    print(f"wrote {len(PEOPLE)} resumes to {args.out}")


if __name__ == "__main__":
    main()
