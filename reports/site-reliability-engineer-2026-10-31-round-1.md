# Screening report: Site Reliability Engineer
Screening round 1 · 2026-10-31 · 100 resumes searched

## Requirements
- 5+ years of experience in DevOps, SRE or platform engineering (must-have)
- Kubernetes and Docker in production (must-have)
- Infrastructure as code with Terraform (must-have)
- AWS or GCP (must-have)
- CI/CD pipelines (GitHub Actions, Jenkins or similar) (must-have)
- Linux (must-have)
- Scripting in Python or Go (must-have)
- Monitoring with Prometheus and Grafana (must-have)
- Incident response and on-call leadership experience (nice-have)
- Cloud cost optimisation (nice-have)

_Assumptions made reading the request: The 5+ years are read as combined experience across DevOps, SRE or platform engineering, not 5 years in each. 'Incident response and on-call leadership' is kept in nice_to_have, because a resume can show on-call or incident lead roles._

## Shortlist
| # | Candidate | Fit | Must-haves met | Round 1 RAG | Recommendation |
|---|---|---|---|---|---|
| 1 | Omar Haddad (`omar_haddad`) | 94 | 8/8 | 98 | Hire |
| 2 | Maria Garcia (`maria_garcia`) | 86 | 7/8 | 97 | Borderline |
| 3 | Elena Rodriguez (`resume_elena_rodriguez`) | 78 | 4/8 | 98 | Borderline |
| 4 | Zainab Yusuf (`zainab_yusuf`) | 72 | 4/8 | 89 | Borderline |
| 5 | Divya Reddy (`divya_reddy`) | 67 | 3/8 | 89 | Borderline |
| 6 | Rebecca Stone (`rebecca_stone`) | 67 | 5/8 | 88 | No hire |
| 7 | Andile Khumalo (`andile_khumalo`) | 67 | 3/8 | 82 | Borderline |
| 8 | Samuel Osei (`samuel_osei`) | 61 | 2/8 | 82 | Borderline |
| 9 | Felix Wagner (`felix_wagner`) | 61 | 3/8 | 78 | No hire |
| 10 | Li Wei (`li_wei`) | 61 | 5/8 | 76 | No hire |

## Candidates
### 1. Omar Haddad (omar_haddad) - Hire, fit 94
Meets every must-have, with evidence quoted from the resume. Resume: `resumes/omar_haddad.md`. Round 1 RAG score 98.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): SRE role from Jan 2021 to Oct 2026 is about 5.8 years, plus Sep 2018 to Dec 2020 systems engineering (about 2.3 years), exceeding 5 years. - "Senior Site Reliability Engineer, Petra Cloud Jan 2021 - Present"
- **Kubernetes and Docker in production** (must-have): Kubernetes is run in production at Petra Cloud, and Docker migration work was done at Levant Hosting. - "Operates 25 GKE Kubernetes clusters on GCP with Terraform modules for every environment."
- **Infrastructure as code with Terraform** (must-have): The candidate uses Terraform modules for every environment in the current role. - "Operates 25 GKE Kubernetes clusters on GCP with Terraform modules for every environment."
- **AWS or GCP** (must-have): The candidate works on GCP in the current role and worked on AWS previously. - "Operates 25 GKE Kubernetes clusters on GCP"
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): The candidate built Jenkins CI/CD pipelines in a job. - "Linux administration, Docker migration and Jenkins CI/CD pipelines on AWS."
- **Linux** (must-have): Linux administration was part of a job. - "Linux administration, Docker migration and Jenkins CI/CD pipelines on AWS."
- **Scripting in Python or Go** (must-have): The candidate wrote Go and Python in the current role. - "Wrote Go operators and Python tooling for automated failover"
- **Monitoring with Prometheus and Grafana** (must-have): The candidate set up Prometheus and Grafana alerting in the current role. - "Prometheus and Grafana alerting."
- **Incident response and on-call leadership experience** (nice-have): The candidate directly leads incident reviews and on-call. - "Leads incident reviews and the on-call rotation for 40 engineers."
**Gaps**
- **Cloud cost optimisation** (nice-have): The resume makes no mention of cloud cost optimisation.

### 2. Maria Garcia (maria_garcia) - Borderline, fit 86
Only partly meets must-have: Monitoring with Prometheus and Grafana. Resume: `resumes/maria_garcia.txt`. Round 1 RAG score 97.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): Indeed Jan 2019–Feb 2021 (~2y2m) plus Dell Mar 2021–Oct 2026 (~5y8m) totals about 7y10m, which is at least 5 years. - "Senior Platform Engineer, Dell Technologies Mar 2021 - Present"
- **Kubernetes and Docker in production** (must-have): She runs Kubernetes clusters at Dell and built Docker images at Indeed, both in jobs. - "Run 40+ Kubernetes clusters with Terraform; built CI/CD with GitHub Actions."
- **Infrastructure as code with Terraform** (must-have): She uses Terraform to manage infrastructure in her current role. - "Run 40+ Kubernetes clusters with Terraform"
- **AWS or GCP** (must-have): She works across both AWS and GCP in her current role. - "Python automation for cost reporting across AWS and GCP."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): She built GitHub Actions CI/CD and Jenkins pipelines in her jobs. - "built CI/CD with GitHub Actions."
- **Linux** (must-have): She managed a Linux fleet at Indeed. - "Jenkins pipelines, Docker images, Linux fleet management."
- **Scripting in Python or Go** (must-have): She does Python automation in her current role. - "Python automation for cost reporting across AWS and GCP."
**Gaps**
- **Monitoring with Prometheus and Grafana** (must-have): Prometheus appears only in the skills list and Grafana is not mentioned at all. - "AWS, GCP, Kubernetes, Docker, Terraform, CI/CD (Jenkins, GitHub Actions), Linux, Bash, Python, Prometheus"
- **Incident response and on-call leadership experience** (nice-have): The resume does not mention incident response or on-call work.
- **Cloud cost optimisation** (nice-have): Cost reporting is related to cost optimisation but does not show actual cost reduction. - "Python automation for cost reporting across AWS and GCP."
**Improvement suggestions**
- Ask directly about incident response and on-call. Have her describe a specific production incident on her 40+ Kubernetes clusters at Dell or the Indeed Linux fleet: her role, how it was detected, escalation, resolution and any postmortem. Also ask whether she has led an on-call rotation, since the resume shows no evidence of this must-have.
- Probe Prometheus hands-on, since it appears only in her skills list. Ask how she has used it on her Kubernetes clusters (exporters, alerting rules, PromQL queries) and whether she has built Grafana dashboards or used an equivalent visualisation tool.
- Ask what decisions came out of her Python cost reporting across AWS and GCP. Request a concrete example where she identified and implemented savings, such as rightsizing, scheduling or commitment purchases, with an approximate percentage or dollar reduction.
- If interview answers on on-call and monitoring are thin, consider a short practical exercise. For example, have her design alerting and dashboards for a Kubernetes service, or walk through triaging a simulated outage, to see whether she can close these gaps quickly.

### 3. Elena Rodriguez (resume_elena_rodriguez) - Borderline, fit 78
Only partly meets must-have: Kubernetes and Docker in production; AWS or GCP; Linux; Monitoring with Prometheus and Grafana. Resume: `resumes/resume_elena_rodriguez.docx`. Round 1 RAG score 98.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): DevOps at Saffron Grid 2016–2021 (5 years) plus SRE at Tidewater 2021–Oct 2026 (about 5.8 years) totals about 10.8 years, which exceeds 5. - "Staff Site Reliability Engineer - Tidewater Robotics (2021 - Present)"
- **Infrastructure as code with Terraform** (must-have): Terraform was used in a job to perform a large migration. - "Migrated 120 virtual machines to Kubernetes with Terraform and Helm."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): The candidate built CI/CD pipelines in a DevOps role. - "Built CI/CD pipelines that reduced deploy time from 45 to 8 minutes."
- **Scripting in Python or Go** (must-have): Python scripting was used in the current role. - "Wrote PYTHON automation that rotates credentials across 300 services with zero downtime."
- **Incident response and on-call leadership experience** (nice-have): The candidate leads incident response in the current staff SRE role. - "Leads incident response and blameless postmortems."
- **Cloud cost optimisation** (nice-have): The resume shows a quantified cloud cost reduction achieved in a job. - "Cut monthly cloud spend by 27% by right-sizing Kubernetes clusters."
**Gaps**
- **Kubernetes and Docker in production** (must-have): Production Kubernetes work is clearly shown in jobs, but Docker appears only in the skills list. - "Migrated 120 virtual machines to Kubernetes with Terraform and Helm."
- **AWS or GCP** (must-have): AWS and GCP appear only in the skills list, and no role names the cloud provider used. - "Cloud | AWS, GCP"
- **Linux** (must-have): Linux is never named; Bash scripting is only related evidence. - "Languages | Go, PYTHON, Bash"
- **Monitoring with Prometheus and Grafana** (must-have): Prometheus and Grafana appear only in the skills list and in no job. - "Observability | Prometheus, Grafana, OpenTelemetry"
**Improvement suggestions**
- Ask which cloud provider(s) hosted the Kubernetes clusters she right-sized at Tidewater Robotics and the VM migration at Saffron Grid Energy, and have her walk through the specific AWS or GCP services she managed. This would resolve the partial AWS/GCP judgement, since neither role names a provider.
- Probe her hands-on Docker production use: how images were built, hardened and shipped in the CI/CD pipelines she built, and how container issues were debugged in the 120-VM migration to Kubernetes. Docker currently appears only in the skills list.
- Ask her to describe a real incident she led at Tidewater, including how Prometheus alerts and Grafana dashboards were used (or which tools were used instead). This would confirm whether her listed observability skills were applied in production.
- Run a short Linux troubleshooting exercise (e.g., diagnosing a degraded node or process) or ask how her Bash and Python scripts interacted with host systems. Linux is never named on the resume, so its depth needs direct verification.

### 4. Zainab Yusuf (zainab_yusuf) - Borderline, fit 72
Only partly meets must-have: Kubernetes and Docker in production; Infrastructure as code with Terraform; Linux; Monitoring with Prometheus and Grafana. Resume: `resumes/zainab_yusuf.txt`. Round 1 RAG score 89.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): Silverpine Jan 2021–Oct 2023 (2y10m) plus Bluefinch Nov 2023–Oct 2026 (3y0m) gives about 5y10m, which is at least 5 years. - "Senior Site Reliability Engineer, Bluefinch Nov 2023 - Present"
- **AWS or GCP** (must-have): GCP was used in a job role. - "Codified environments with GCP, replacing hand-built servers."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): The candidate built CI/CD pipelines in both roles, and GitLab CI is similar to the tools named. - "Built CI/CD pipelines with GitLab CI that cut deployment time by 40%."
- **Scripting in Python or Go** (must-have): Go was used in a current job role. - "Built CI/CD pipelines with Go that cut deployment time by 30%."
- **Incident response and on-call leadership experience** (nice-have): The candidate led incident response in a current role, and reducing pages implies on-call involvement. - "Led incident response and wrote postmortems; raised availability to 99.94.7%."
**Gaps**
- **Kubernetes and Docker in production** (must-have): Kubernetes and Docker appear only in the summary and skills list, with no job bullet showing production use. - "DevOps engineer with 5 years of experience, most recently working with Kubernetes, GCP, Terraform."
- **Infrastructure as code with Terraform** (must-have): Terraform is named only in the summary and skills list; the codifying bullet in a job mentions GCP, not Terraform. - "DevOps engineer with 5 years of experience, most recently working with Kubernetes, GCP, Terraform."
- **Linux** (must-have): Linux appears only in the skills list. - "Linux, Docker, GCP, GitLab CI, Kubernetes, Terraform, Go"
- **Monitoring with Prometheus and Grafana** (must-have): The resume shows alerting and SLO work, but Prometheus and Grafana are not named. - "Introduced SLOs and alerting that reduced pages per week by 30%."
- **Cloud cost optimisation** (nice-have): The resume does not mention cloud cost optimisation.
**Round 1 rule checks** (Milestone 2's vocabulary and date arithmetic, shown for comparison; Round 2's judgement above is the one that counts)
- AWS or GCP (has AWS missing)
- Scripting in Python or Go (has Python missing)
**Improvement suggestions**
- In the interview, ask for a concrete production Kubernetes and Docker example, such as cluster size, how workloads were deployed, and an issue they debugged. These tools appear only in the summary and skills list, not in any job bullet.
- Ask what tool they used to codify GCP environments at Silverpine and request a Terraform sample, such as a module structure or how they handled state and drift. The resume never ties Terraform to a specific role.
- Probe the Bluefinch SLO and alerting work by asking which monitoring stack they used and whether they built Prometheus rules or Grafana dashboards. Also ask them to clarify the availability figure, which is written as "99.94.7%" on the resume.
- Ask whether they have done any GCP cost work, such as rightsizing, committed-use discounts, or autoscaling tuning, and what savings resulted. If they have none, treat cost optimisation as a gap to close through onboarding or a short take-home exercise.

### 5. Divya Reddy (divya_reddy) - Borderline, fit 67
Only partly meets must-have: Kubernetes and Docker in production; AWS or GCP; Linux; Scripting in Python or Go; Monitoring with Prometheus and Grafana. Resume: `resumes/divya_reddy.md`. Round 1 RAG score 89.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): DevOps Engineer from Mar 2019 to Feb 2023 is about 4 years, and SRE from Mar 2023 to Oct 2026 is about 3.6 years, totalling about 7.6 years, which is at least 5. - "Senior Site Reliability Engineer, Northgate Travel Mar 2023 - Present"
- **Infrastructure as code with Terraform** (must-have): The current SRE role explicitly uses Terraform for infrastructure as code. - "Codified environments with Terraform, replacing hand-built servers."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): The Trellis Health role shows Jenkins CI/CD pipelines built on the job. - "Built CI/CD pipelines with Jenkins that cut deployment time by 18%."
- **Incident response and on-call leadership experience** (nice-have): The candidate explicitly led incident response in the current role. - "Led incident response and wrote postmortems; raised availability to 99.94.8%."
**Gaps**
- **Kubernetes and Docker in production** (must-have): Kubernetes and Docker appear only in the skills list and summary, with no job showing production use. - "Linux, Python, Docker, Jenkins, Kubernetes, AWS, Terraform, System Design"
- **AWS or GCP** (must-have): AWS is named only in the summary and skills list, not in any job description. - "most recently working with Kubernetes, AWS, Terraform."
- **Linux** (must-have): Linux appears only in the skills list and in no job description. - "Linux, Python, Docker, Jenkins, Kubernetes, AWS, Terraform, System Design"
- **Scripting in Python or Go** (must-have): Python appears only in the skills list, with no scripting shown in any job. - "Linux, Python, Docker, Jenkins, Kubernetes, AWS, Terraform, System Design"
- **Monitoring with Prometheus and Grafana** (must-have): There is alerting work, but Prometheus and Grafana are never named. - "Introduced SLOs and alerting that reduced pages per week by 18%."
- **Cloud cost optimisation** (nice-have): Nothing in the resume mentions cloud cost optimisation.
**Improvement suggestions**
- In the interview, ask her to walk through a specific production Kubernetes and Docker setup she ran on AWS at Northgate Travel or Trellis Health: cluster size, how deployments worked, and an issue she debugged. The resume lists both only as skills, with no job showing production use.
- Ask what tools sat behind the SLOs and alerting at Trellis Health and whether Prometheus and Grafana were involved. If not, find out how she would move her alerting experience onto that stack.
- Request a sample or detailed description of Python scripts she has written for automation or tooling, and include a short practical Linux and Python troubleshooting exercise. Both appear only in her skills list.
- Ask directly whether she has done any cloud cost optimisation work, such as rightsizing, reserved capacity or cost monitoring, since the resume mentions none. Also ask her to clarify the '99.94.8%' availability figure and what 'CI/CD pipelines with System Design' meant in practice.

### 6. Rebecca Stone (rebecca_stone) - No hire, fit 67
Misses must-have: Monitoring with Prometheus and Grafana. Resume: `resumes/rebecca_stone.txt`. Round 1 RAG score 88.
**Strengths**
- **Infrastructure as code with Terraform** (must-have): Terraform is used for infrastructure design in the current role. - "Designed multi-account AWS and Azure landing zones with Terraform for banks and insurers."
- **AWS or GCP** (must-have): AWS work appears across two roles. - "Migrated on-premise Linux workloads to AWS; Python automation and Jenkins pipelines."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): Jenkins pipelines were used in a job. - "Migrated on-premise Linux workloads to AWS; Python automation and Jenkins pipelines."
- **Linux** (must-have): Linux administration and Linux workload migration appear in jobs. - "Linux and VMware administration."
- **Scripting in Python or Go** (must-have): Python automation was done in the Cloud Engineer role. - "Migrated on-premise Linux workloads to AWS; Python automation and Jenkins pipelines."
**Gaps**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): The Cloud Engineer role (Mar 2014 - Jan 2020, about 5.8 years) is DevOps-adjacent, and the later role is consulting architecture, so neither is explicitly DevOps, SRE or platform engineering. - "Migrated on-premise Linux workloads to AWS; Python automation and Jenkins pipelines."
- **Kubernetes and Docker in production** (must-have): Kubernetes appears only in an advisory capacity and Docker only in the skills list, with no hands-on production operation shown. - "Advised clients on Kubernetes adoption and CI/CD standards; pre-sales architecture reviews."
- **Monitoring with Prometheus and Grafana** (must-have): There is no mention of Prometheus, Grafana or monitoring.
- **Incident response and on-call leadership experience** (nice-have): There is no mention of incident response or on-call work.
- **Cloud cost optimisation** (nice-have): There is no mention of cloud cost optimisation.

### 7. Andile Khumalo (andile_khumalo) - Borderline, fit 67
Only partly meets must-have: Kubernetes and Docker in production; Infrastructure as code with Terraform; Linux; Scripting in Python or Go; Monitoring with Prometheus and Grafana. Resume: `resumes/andile_khumalo.txt`. Round 1 RAG score 82.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): Stratawave Oct 2021–Nov 2023 (~2y2m) plus Ironbark Dec 2023–Oct 2026 (~2y11m) gives about 5y1m, meeting 5+ years. - "DevOps Engineer, Ironbark Security Dec 2023 - Present"
- **AWS or GCP** (must-have): AWS is used in production in the current role. - "Ran production infrastructure on Kubernetes and AWS for 4 product teams."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): The candidate built CI/CD pipelines with Jenkins in a job. - "Built CI/CD pipelines with Jenkins that cut deployment time by 25%."
- **Incident response and on-call leadership experience** (nice-have): The candidate explicitly led incident response in a role. - "Led incident response and wrote postmortems"
**Gaps**
- **Kubernetes and Docker in production** (must-have): Kubernetes in production is shown, but Docker appears only in the skills list. - "Ran production infrastructure on Kubernetes and AWS for 4 product teams."
- **Infrastructure as code with Terraform** (must-have): Infrastructure codification is done with Helm, a neighbouring tool, not Terraform. - "Codified environments with Helm, replacing hand-built servers."
- **Linux** (must-have): Linux appears only in the skills list, not in any role. - "Linux, Docker, Bash, Jenkins, Kubernetes, AWS, Helm, Prometheus"
- **Scripting in Python or Go** (must-have): Only Bash is listed, a neighbouring scripting language, and only in the skills list; no Python or Go. - "Linux, Docker, Bash, Jenkins, Kubernetes, AWS, Helm, Prometheus"
- **Monitoring with Prometheus and Grafana** (must-have): Alerting work is shown and Prometheus is in the skills list, but Grafana is absent and Prometheus is not tied to a role. - "Introduced SLOs and alerting that reduced pages per week by 25%."
- **Cloud cost optimisation** (nice-have): Nothing in the resume mentions cloud cost optimisation.
**Round 1 rule checks** (Milestone 2's vocabulary and date arithmetic, shown for comparison; Round 2's judgement above is the one that counts)
- Infrastructure as code with Terraform (has Terraform missing)
- Scripting in Python or Go (has Python missing)
**Improvement suggestions**
- Ask whether Andile has provisioned AWS resources (networking, IAM, clusters) with Terraform, since the resume shows only Helm, which packages Kubernetes deployments rather than provisioning cloud infrastructure. If not, a short take-home Terraform exercise would show how quickly the gap could close.
- Request a Python or Go code sample, or run a short live scripting exercise. The resume lists only Bash, and only in the skills list, so any Python or Go ability needs direct evidence.
- Have them walk through the SLOs and alerting they introduced at Ironbark Security: which tools they used, whether Prometheus and Grafana were involved, and how they debugged Docker containers and Linux hosts during incidents. Also ask them to clarify the availability figure, which is written as "99.94.8%" on the resume.
- Ask whether they did any cost tracking or optimisation while running AWS infrastructure for 4 product teams, since cloud cost optimisation is the one requirement with no evidence at all.

### 8. Samuel Osei (samuel_osei) - Borderline, fit 61
Only partly meets must-have: Kubernetes and Docker in production; Infrastructure as code with Terraform; AWS or GCP; Linux; Scripting in Python or Go; Monitoring with Prometheus and Grafana. Resume: `resumes/samuel_osei.md`. Round 1 RAG score 82.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): DevOps Engineer Jul 2019–Jun 2022 (3 yrs) plus SRE Jul 2022–Oct 2026 (~4.3 yrs) totals ~7.3 years, above 5. - "Senior Site Reliability Engineer, Ember Analytics Jul 2022 - Present"
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): The candidate built CI/CD pipelines in the current role, and Jenkins is also listed in skills. - "Built CI/CD pipelines with Prometheus that cut deployment time by 18%."
- **Incident response and on-call leadership experience** (nice-have): The candidate led incident response and reduced pages, showing incident response and on-call leadership. - "Led incident response and wrote postmortems; raised availability to 99.94.7%."
**Gaps**
- **Kubernetes and Docker in production** (must-have): Kubernetes appears only in the summary and skills, not in any role, and Docker is not mentioned at all. - "most recently working with Kubernetes, AWS, Terraform."
- **Infrastructure as code with Terraform** (must-have): Terraform is listed in the summary and skills, but no role describes using it; infrastructure was codified with Bash instead. - "most recently working with Kubernetes, AWS, Terraform."
- **AWS or GCP** (must-have): AWS appears only in the summary and skills list, with no job bullet describing AWS work. - "most recently working with Kubernetes, AWS, Terraform."
- **Linux** (must-have): Linux appears only in the skills list and in no role. - "Linux, AWS, Bash, Jenkins, Kubernetes, Terraform, Prometheus"
- **Scripting in Python or Go** (must-have): Only Bash scripting is shown, which is a neighbouring language rather than Python or Go. - "Codified environments with Bash, replacing hand-built servers."
- **Monitoring with Prometheus and Grafana** (must-have): Prometheus is used in a role, but Grafana is not mentioned anywhere. - "Built CI/CD pipelines with Prometheus that cut deployment time by 18%."
- **Cloud cost optimisation** (nice-have): Nothing in the resume mentions cloud cost optimisation.
**Round 1 rule checks** (Milestone 2's vocabulary and date arithmetic, shown for comparison; Round 2's judgement above is the one that counts)
- Kubernetes and Docker in production (has Docker missing)
- Scripting in Python or Go (has Python missing)
**Improvement suggestions**
- In the interview, have him walk through the Kubernetes and AWS setup behind his Senior SRE work at Ember Analytics, including how services were containerised, since Docker is never mentioned and neither technology appears in a job bullet.
- Ask for a Terraform sample (a module or repo excerpt) or a detailed account of how he managed state and environments. Also ask whether the Bash-based environment codification at Solace Bank was ever moved to Terraform.
- Probe the Python/Go gap directly by asking for any Python or Go code he has written, or by setting a short scripting exercise. If he has only Bash, decide whether he could reasonably ramp up on the job.
- Clarify the unclear resume details: the '99.94.7%' availability figure, which tools the CI/CD pipelines were built on (the bullet cites Prometheus; Jenkins is in his skills), and whether he used Grafana for dashboards. Also ask whether he has done any cloud cost optimisation work, since none is listed.

### 9. Felix Wagner (felix_wagner) - No hire, fit 61
Misses must-have: Monitoring with Prometheus and Grafana. Resume: `resumes/felix_wagner.docx`. Round 1 RAG score 78.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): Stratawave Apr 2017–Mar 2022 (5 years) plus Arclight Apr 2022–Oct 2026 (4.5 years) totals about 9.5 years, which exceeds the 5 required. - "DevOps Engineer, Stratawave Apr 2017 - Mar 2022"
- **Infrastructure as code with Terraform** (must-have): The current SRE role describes using Terraform for infrastructure as code. - "Codified environments with Terraform, replacing hand-built servers."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): Both roles describe building CI/CD pipelines. - "Built CI/CD pipelines with Bash that cut deployment time by 40%."
- **Incident response and on-call leadership experience** (nice-have): The current role explicitly states he led incident response and wrote postmortems. - "Led incident response and wrote postmortems; raised availability to 99.94.8%."
**Gaps**
- **Kubernetes and Docker in production** (must-have): Kubernetes appears only in the summary and skills list, with no job describing production use, and Docker is not mentioned. - "most recently working with Kubernetes, Azure, Terraform."
- **AWS or GCP** (must-have): The candidate uses Azure, a neighbouring cloud, rather than AWS or GCP. - "most recently working with Kubernetes, Azure, Terraform."
- **Linux** (must-have): Linux appears only in the skills list and in no job description. - "Linux, VMware, Ansible, Bash, Kubernetes, Azure, Terraform, CI/CD"
- **Scripting in Python or Go** (must-have): The resume shows Bash scripting, a neighbouring language, but no Python or Go. - "Built CI/CD pipelines with Bash that cut deployment time by 40%."
- **Monitoring with Prometheus and Grafana** (must-have): Prometheus and Grafana are not mentioned anywhere in the resume.
- **Cloud cost optimisation** (nice-have): The resume contains nothing about cloud cost optimisation.
**Round 1 rule checks** (Milestone 2's vocabulary and date arithmetic, shown for comparison; Round 2's judgement above is the one that counts)
- Kubernetes and Docker in production (has Docker missing)
- AWS or GCP (has AWS missing)
- Scripting in Python or Go (has Python missing)

### 10. Li Wei (li_wei) - No hire, fit 61
Misses must-have: Linux; Monitoring with Prometheus and Grafana. Resume: `resumes/li_wei.txt`. Round 1 RAG score 76.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): ML platform engineering roles: Mar 2020–Mar 2022 (2 yrs) + Apr 2022–Oct 2026 (~4.6 yrs) ≈ 6.6 years, which is at least 5, though the focus is ML-specific platform work. - "Machine Learning Platform Engineer, Shopee"
- **Kubernetes and Docker in production** (must-have): Kubernetes serves 300+ models in production at Grab, and Docker was used to containerise training jobs at Shopee. - "Built a Kubeflow and MLflow based model platform on Kubernetes serving 300+ ML models."
- **AWS or GCP** (must-have): GCP was used for model deployment in the Shopee role. - "CI/CD for model deployment on GCP."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): The candidate built CI/CD for model deployment at Shopee, although no specific tool is named. - "Containerised training jobs with Docker; CI/CD for model deployment on GCP."
- **Scripting in Python or Go** (must-have): The candidate built a Python SDK in the current Grab role. - "Python SDK for feature store access; Airflow retraining pipelines."
**Gaps**
- **Infrastructure as code with Terraform** (must-have): Terraform appears only in the skills list and is not tied to any role. - "Python, Kubernetes, Kubeflow, MLflow, Docker, Terraform, AWS, GCP"
- **Linux** (must-have): Linux is not mentioned anywhere in the resume.
- **Monitoring with Prometheus and Grafana** (must-have): Neither Prometheus nor Grafana is mentioned.
- **Incident response and on-call leadership experience** (nice-have): The resume does not mention incident response or on-call leadership.
- **Cloud cost optimisation** (nice-have): Cloud cost optimisation is not mentioned.
**Round 1 rule checks** (Milestone 2's vocabulary and date arithmetic, shown for comparison; Round 2's judgement above is the one that counts)
- Linux (has Linux missing)

## How to read this report
- **Round 1** ranked every resume with Milestone 2's hybrid search (embeddings, BM25, skill match) and kept the top 10; on a re-screen the previous shortlist is carried forward too, so nobody leaves the list because the search changed. Nobody is rejected at this stage.
- **Round 2**: Claude judged each requirement as met, partial or missing, quoting the resume. Fit = weighted share met (must-have x2, nice-to-have x1; partial = half). A 'met' whose quote is not in the resume counts as partial.
- **Round 3**: Hire = every must-have met; No hire = a must-have missing; Borderline = in between.
- Requirements a resume cannot show (communication, attitude, working style) are interview checks: listed above, but they affect neither the fit score nor the recommendation.
- These are screening recommendations for a human decision-maker, not hiring decisions.
