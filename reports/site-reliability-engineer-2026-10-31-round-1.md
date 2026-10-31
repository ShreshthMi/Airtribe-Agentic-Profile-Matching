# Screening report: Site Reliability Engineer
Screening round 1 · 2026-10-31 · 100 resumes searched

## Requirements
- 5+ years of experience in DevOps, SRE or platform engineering (must-have)
- Kubernetes in production (must-have)
- Docker in production (must-have)
- Infrastructure as code with Terraform (must-have)
- Experience with AWS or GCP (must-have)
- CI/CD pipelines (GitHub Actions, Jenkins or similar) (must-have)
- Linux (must-have)
- Scripting in Python or Go (must-have)
- Monitoring with Prometheus and Grafana (must-have)
- Incident response and on-call leadership (nice-have)
- Cloud cost optimisation (nice-have)

_Assumptions made reading the request: Read the 5+ years as total experience across DevOps, SRE or platform engineering combined, not 5+ years in each. 'Kubernetes and Docker in production' was split into two separate checks, both requiring production use. 'Python or Go' and 'AWS or GCP' are each satisfied by either option._

## Shortlist
| # | Candidate | Fit | Must-haves met | Round 1 RAG | Recommendation |
|---|---|---|---|---|---|
| 1 | Omar Haddad (`omar_haddad`) | 95 | 9/9 | 98 | Hire |
| 2 | Maria Garcia (`maria_garcia`) | 88 | 8/9 | 97 | Borderline |
| 3 | Elena Rodriguez (`resume_elena_rodriguez`) | 80 | 5/9 | 99 | Borderline |
| 4 | Zainab Yusuf (`zainab_yusuf`) | 70 | 4/9 | 89 | Borderline |
| 5 | Rebecca Stone (`rebecca_stone`) | 70 | 6/9 | 88 | No hire |
| 6 | Divya Reddy (`divya_reddy`) | 65 | 3/9 | 89 | Borderline |
| 7 | Andile Khumalo (`andile_khumalo`) | 65 | 3/9 | 82 | Borderline |
| 8 | Li Wei (`li_wei`) | 60 | 5/9 | 80 | No hire |
| 9 | Samuel Osei (`samuel_osei`) | 55 | 2/9 | 82 | No hire |
| 10 | Felix Wagner (`felix_wagner`) | 55 | 3/9 | 78 | No hire |

## Candidates
### 1. Omar Haddad (omar_haddad) - Hire, fit 95
Meets every must-have, with evidence quoted from the resume. Resume: `resumes/omar_haddad.md`. Round 1 RAG score 98.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): The SRE role runs from Jan 2021 to Oct 2026, about 5 years 10 months, which meets 5+ years without counting the Sep 2018 - Dec 2020 systems role (2 years 4 months). - "Senior Site Reliability Engineer, Petra Cloud Jan 2021 - Present"
- **Kubernetes in production** (must-have): He operates multiple production GKE clusters in his current role. - "Operates 25 GKE Kubernetes clusters on GCP with Terraform modules for every environment."
- **Docker in production** (must-have): He led a Docker migration in a hosting job, which shows Docker used in production. - "Linux administration, Docker migration and Jenkins CI/CD pipelines on AWS."
- **Infrastructure as code with Terraform** (must-have): Terraform modules are used for every environment in his current role. - "Operates 25 GKE Kubernetes clusters on GCP with Terraform modules for every environment."
- **Experience with AWS or GCP** (must-have): He uses GCP in his current role and used AWS in his previous role. - "Operates 25 GKE Kubernetes clusters on GCP with Terraform modules for every environment."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): He built Jenkins CI/CD pipelines in a job. - "Linux administration, Docker migration and Jenkins CI/CD pipelines on AWS."
- **Linux** (must-have): Linux administration was part of a role. - "Linux administration, Docker migration and Jenkins CI/CD pipelines on AWS."
- **Scripting in Python or Go** (must-have): He wrote both Go and Python tooling on the job. - "Wrote Go operators and Python tooling for automated failover; Prometheus and Grafana alerting."
- **Monitoring with Prometheus and Grafana** (must-have): Prometheus and Grafana alerting are part of his current role. - "Wrote Go operators and Python tooling for automated failover; Prometheus and Grafana alerting."
- **Incident response and on-call leadership** (nice-have): He leads incident reviews and an on-call rotation of 40 engineers. - "Leads incident reviews and the on-call rotation for 40 engineers."
**Gaps**
- **Cloud cost optimisation** (nice-have): The resume makes no mention of cloud cost optimisation.

### 2. Maria Garcia (maria_garcia) - Borderline, fit 88
Only partly meets must-have: Monitoring with Prometheus and Grafana. Resume: `resumes/maria_garcia.txt`. Round 1 RAG score 97.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): Dell Mar 2021–Oct 2026 is about 5.6 years plus Indeed Jan 2019–Feb 2021 at about 2.1 years, totalling about 7.7 years, which is at least 5. - "Senior Platform Engineer, Dell Technologies Mar 2021 - Present"
- **Kubernetes in production** (must-have): Running 40+ Kubernetes clusters in a current job shows production Kubernetes use. - "Run 40+ Kubernetes clusters with Terraform; built CI/CD with GitHub Actions."
- **Docker in production** (must-have): Docker image work is listed as part of the DevOps role at Indeed. - "Jenkins pipelines, Docker images, Linux fleet management."
- **Infrastructure as code with Terraform** (must-have): Terraform is used to manage clusters in the current role. - "Run 40+ Kubernetes clusters with Terraform; built CI/CD with GitHub Actions."
- **Experience with AWS or GCP** (must-have): The current role involves work across both AWS and GCP. - "Python automation for cost reporting across AWS and GCP."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): She built CI/CD with GitHub Actions and also ran Jenkins pipelines at Indeed. - "Run 40+ Kubernetes clusters with Terraform; built CI/CD with GitHub Actions."
- **Linux** (must-have): Linux fleet management is part of a job. - "Jenkins pipelines, Docker images, Linux fleet management."
- **Scripting in Python or Go** (must-have): Python automation is used in the current role. - "Python automation for cost reporting across AWS and GCP."
**Gaps**
- **Monitoring with Prometheus and Grafana** (must-have): Prometheus appears only in the skills list and Grafana is not mentioned anywhere. - "AWS, GCP, Kubernetes, Docker, Terraform, CI/CD (Jenkins, GitHub Actions), Linux, Bash, Python, Prometheus"
- **Incident response and on-call leadership** (nice-have): The resume does not mention incident response or on-call work.
- **Cloud cost optimisation** (nice-have): Cost reporting is related to cost optimisation, but the resume does not show actual cost reductions. - "Python automation for cost reporting across AWS and GCP."
**Improvement suggestions**
- In the interview, ask how incidents and on-call were handled for the 40+ Kubernetes clusters at Dell, and whether she has led incident response, run postmortems or owned an on-call rotation. The resume never mentions this must-have, so it is the main gap to close.
- Ask her to walk through how she used Prometheus on those clusters (alerting rules, exporters, dashboards) and whether she has worked with Grafana or a similar visualisation tool. Prometheus appears only in her skills list and Grafana does not appear at all.
- Ask whether the Python cost reporting she built across AWS and GCP led to any concrete savings, such as rightsizing, reserved or committed-use purchases or idle resource cleanup, and request figures or examples. This would show whether her cost experience goes beyond reporting.
- Confirm her total experience, since her summary says 6 years while the dates listed (Jan 2019 to present) suggest more. Either figure meets the 5+ year requirement, so this only matters for accuracy.

### 3. Elena Rodriguez (resume_elena_rodriguez) - Borderline, fit 80
Only partly meets must-have: Docker in production; Experience with AWS or GCP; Linux; Monitoring with Prometheus and Grafana. Resume: `resumes/resume_elena_rodriguez.docx`. Round 1 RAG score 99.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): DevOps 2016-2021 (5 years) plus Staff SRE 2021-Present (about 5.8 years) totals about 10.8 years, which exceeds 5. - "DevOps Engineer - Saffron Grid Energy (2016 - 2021)"
- **Kubernetes in production** (must-have): Two jobs show Kubernetes work: managing clusters at Tidewater and migrating VMs to Kubernetes at Saffron Grid. - "Cut monthly cloud spend by 27% by right-sizing Kubernetes clusters."
- **Infrastructure as code with Terraform** (must-have): Terraform was used in a job to carry out a large migration. - "Migrated 120 virtual machines to Kubernetes with Terraform and Helm."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): The candidate built CI/CD pipelines in a role, although the tool is not named. - "Built CI/CD pipelines that reduced deploy time from 45 to 8 minutes."
- **Scripting in Python or Go** (must-have): The candidate wrote Python automation in a current role. - "Wrote PYTHON automation that rotates credentials across 300 services with zero downtime."
- **Incident response and on-call leadership** (nice-have): The candidate leads incident response in the current role. - "Leads incident response and blameless postmortems."
- **Cloud cost optimisation** (nice-have): The resume shows a concrete cloud cost reduction achieved in a job. - "Cut monthly cloud spend by 27% by right-sizing Kubernetes clusters."
**Gaps**
- **Docker in production** (must-have): Docker appears only in the skills list and in no described job. - "Containers | Docker, Kubernetes, Helm"
- **Experience with AWS or GCP** (must-have): AWS and GCP appear only in the skills list, and no job names a specific cloud provider. - "Cloud | AWS, GCP"
- **Linux** (must-have): Linux is never mentioned; Bash scripting is only related evidence. - "Languages | Go, PYTHON, Bash"
- **Monitoring with Prometheus and Grafana** (must-have): Prometheus and Grafana appear only in the skills list and in no described job. - "Observability | Prometheus, Grafana, OpenTelemetry"
**Improvement suggestions**
- Ask her which cloud provider (AWS or GCP) hosted the Kubernetes clusters she right-sized at Tidewater Robotics, and which services drove the 27% spend reduction. This would show whether her AWS/GCP experience was hands-on in production or only appears in her skills list.
- In the interview, have her walk through how Prometheus and Grafana were used in her incident response at Tidewater, such as which alerts, dashboards or SLOs she built or relied on. This would confirm that the monitoring tools in her skills list were used in a real job.
- Probe her Docker and Linux depth with questions tied to the Saffron Grid migration of 120 VMs to Kubernetes. Ask how she containerised the workloads, how images were built and kept small, and how she debugged Linux host or container issues during the move.
- Ask which tool her Saffron Grid CI/CD pipelines were built on and whether they built and pushed Docker images. Her answer would settle both the unnamed CI/CD tool and the missing evidence of Docker in production.

### 4. Zainab Yusuf (zainab_yusuf) - Borderline, fit 70
Only partly meets must-have: Kubernetes in production; Docker in production; Infrastructure as code with Terraform; Linux; Monitoring with Prometheus and Grafana. Resume: `resumes/zainab_yusuf.txt`. Round 1 RAG score 89.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): Jan 2021–Oct 2023 (~2.8 years) plus Nov 2023–Oct 2026 (~3 years) is about 5.8 years, which meets 5+. - "Senior Site Reliability Engineer, Bluefinch Nov 2023 - Present"
- **Experience with AWS or GCP** (must-have): GCP was used in a job role. - "Codified environments with GCP, replacing hand-built servers."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): The candidate built CI/CD pipelines with GitLab CI, a tool similar to the ones named. - "Built CI/CD pipelines with GitLab CI that cut deployment time by 40%."
- **Scripting in Python or Go** (must-have): Go was used in a current job role. - "Built CI/CD pipelines with Go that cut deployment time by 30%."
- **Incident response and on-call leadership** (nice-have): The candidate explicitly led incident response in a current role. - "Led incident response and wrote postmortems; raised availability to 99.94.7%."
**Gaps**
- **Kubernetes in production** (must-have): Kubernetes appears only in the summary and skills list, with no job bullet showing production use. - "DevOps engineer with 5 years of experience, most recently working with Kubernetes, GCP, Terraform."
- **Docker in production** (must-have): Docker is listed only in the skills section and appears in no role. - "Linux, Docker, GCP, GitLab CI, Kubernetes, Terraform, Go"
- **Infrastructure as code with Terraform** (must-have): Terraform appears only in the summary and skills list, and the infrastructure-codifying bullet names GCP, not Terraform. - "DevOps engineer with 5 years of experience, most recently working with Kubernetes, GCP, Terraform."
- **Linux** (must-have): Linux appears only in the skills list. - "Linux, Docker, GCP, GitLab CI, Kubernetes, Terraform, Go"
- **Monitoring with Prometheus and Grafana** (must-have): The resume shows monitoring and alerting work but never names Prometheus or Grafana. - "Introduced SLOs and alerting that reduced pages per week by 30%."
- **Cloud cost optimisation** (nice-have): Nothing in the resume mentions cloud cost optimisation.
**Round 1 rule checks** (Milestone 2's vocabulary and date arithmetic, shown for comparison; Round 2's judgement above is the one that counts)
- Experience with AWS or GCP (has AWS missing)
- Scripting in Python or Go (has Python missing)
**Improvement suggestions**
- In the interview, have her walk through a production Kubernetes and Docker setup she ran at Bluefinch or Silverpine Energy: cluster size, how workloads were containerised and deployed, and a failure she debugged. Neither appears in any job bullet, only in the summary and skills list.
- Ask which tool she used to codify GCP environments at Silverpine Energy, and request a Terraform sample or a description of her module, state and plan/apply workflow. The bullet names GCP but not Terraform.
- Ask what stack backed the SLOs and alerting that cut pages by 30%, and whether she built Prometheus metrics or Grafana dashboards herself. Use the same discussion to check the Linux troubleshooting depth behind that work.
- Ask whether she has done any cloud cost optimisation, which is missing from the resume, such as GCP rightsizing or committed-use discounts, and get specific savings figures. Also clarify the malformed '99.94.7%' availability figure.

### 5. Rebecca Stone (rebecca_stone) - No hire, fit 70
Misses must-have: Monitoring with Prometheus and Grafana. Resume: `resumes/rebecca_stone.txt`. Round 1 RAG score 88.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): Cloud Engineer Mar 2014–Jan 2020 is about 5 years 10 months of hands-on automation and pipeline work, which meets 5+ years; the later architect role adds more cloud infrastructure work. - "Migrated on-premise Linux workloads to AWS; Python automation and Jenkins pipelines."
- **Infrastructure as code with Terraform** (must-have): Terraform is used directly for infrastructure in her current role. - "Designed multi-account AWS and Azure landing zones with Terraform for banks and insurers."
- **Experience with AWS or GCP** (must-have): AWS is used across both of her cloud roles since 2014. - "Migrated on-premise Linux workloads to AWS; Python automation and Jenkins pipelines."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): She built Jenkins pipelines in her Cloud Engineer role. - "Migrated on-premise Linux workloads to AWS; Python automation and Jenkins pipelines."
- **Linux** (must-have): She did Linux administration and Linux workload migrations in two roles. - "Linux and VMware administration."
- **Scripting in Python or Go** (must-have): Python automation is shown in a job. - "Migrated on-premise Linux workloads to AWS; Python automation and Jenkins pipelines."
**Gaps**
- **Kubernetes in production** (must-have): Kubernetes appears only as advisory work, with no hands-on production operation shown. - "Advised clients on Kubernetes adoption and CI/CD standards; pre-sales architecture reviews."
- **Docker in production** (must-have): Docker is listed only in the skills section and appears in no job. - "AWS, Azure, Terraform, Kubernetes, Docker, CI/CD, Linux, Python, System Design"
- **Monitoring with Prometheus and Grafana** (must-have): Neither Prometheus nor Grafana, nor any monitoring work, is mentioned.
- **Incident response and on-call leadership** (nice-have): There is no mention of incident response or on-call duties.
- **Cloud cost optimisation** (nice-have): There is no mention of cloud cost optimisation.

### 6. Divya Reddy (divya_reddy) - Borderline, fit 65
Only partly meets must-have: Kubernetes in production; Docker in production; Experience with AWS or GCP; Linux; Scripting in Python or Go; Monitoring with Prometheus and Grafana. Resume: `resumes/divya_reddy.md`. Round 1 RAG score 89.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): DevOps Engineer Mar 2019–Feb 2023 (~4 years) plus SRE Mar 2023–Oct 2026 (~3.6 years) gives ~7.6 years, which is at least 5. - "Senior Site Reliability Engineer, Northgate Travel Mar 2023 - Present"
- **Infrastructure as code with Terraform** (must-have): The current SRE role shows infrastructure as code with Terraform. - "Codified environments with Terraform, replacing hand-built servers."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): The candidate built Jenkins CI/CD pipelines in a job. - "Built CI/CD pipelines with Jenkins that cut deployment time by 18%."
- **Incident response and on-call leadership** (nice-have): The candidate explicitly led incident response in the current role. - "Led incident response and wrote postmortems; raised availability to 99.94.8%."
**Gaps**
- **Kubernetes in production** (must-have): Kubernetes appears only in the summary and skills list, and no job bullet describes production use. - "DevOps engineer with 7 years of experience, most recently working with Kubernetes, AWS, Terraform."
- **Docker in production** (must-have): Docker appears only in the skills list and in no role. - "Linux, Python, Docker, Jenkins, Kubernetes, AWS, Terraform, System Design"
- **Experience with AWS or GCP** (must-have): AWS appears only in the summary and skills list, with no job bullet showing its use. - "DevOps engineer with 7 years of experience, most recently working with Kubernetes, AWS, Terraform."
- **Linux** (must-have): Linux appears only in the skills list. - "Linux, Python, Docker, Jenkins, Kubernetes, AWS, Terraform, System Design"
- **Scripting in Python or Go** (must-have): Python appears only in the skills list, with no scripting described in any role. - "Linux, Python, Docker, Jenkins, Kubernetes, AWS, Terraform, System Design"
- **Monitoring with Prometheus and Grafana** (must-have): The resume shows alerting work, but Prometheus and Grafana are never named. - "Introduced SLOs and alerting that reduced pages per week by 18%."
- **Cloud cost optimisation** (nice-have): Nothing in the resume mentions cloud cost optimisation.
**Improvement suggestions**
- In the interview, have her walk through a specific production Kubernetes and Docker setup she ran at Northgate Travel or Trellis Health, covering cluster size, deployment strategy and a failure she debugged. Kubernetes and Docker appear only in her summary and skills list, not in any role.
- Ask which AWS services her Terraform code provisioned in the current SRE role, and request a sanitised Terraform module or architecture diagram. This would confirm hands-on AWS use, which currently rests only on her summary and skills list.
- Ask which tools sat behind the SLOs and alerting she introduced at Trellis Health, to confirm whether she used Prometheus and Grafana. Also ask for an example Python script she wrote for operations work, since Python is listed only as a skill.
- Ask her to clarify two unclear claims: the '99.94.8%' availability figure and 'CI/CD pipelines with System Design'. Also probe whether she has done any cloud cost optimisation, which is a must-have missing from her resume.

### 7. Andile Khumalo (andile_khumalo) - Borderline, fit 65
Only partly meets must-have: 5+ years of experience in DevOps, SRE or platform engineering; Docker in production; Infrastructure as code with Terraform; Linux; Scripting in Python or Go; Monitoring with Prometheus and Grafana. Resume: `resumes/andile_khumalo.txt`. Round 1 RAG score 82.
**Strengths**
- **Kubernetes in production** (must-have): The current role explicitly involves running production infrastructure on Kubernetes. - "Ran production infrastructure on Kubernetes and AWS for 4 product teams."
- **Experience with AWS or GCP** (must-have): The current role shows production AWS experience. - "Ran production infrastructure on Kubernetes and AWS for 4 product teams."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): The candidate built Jenkins CI/CD pipelines in a job. - "Built CI/CD pipelines with Jenkins that cut deployment time by 25%."
- **Incident response and on-call leadership** (nice-have): The candidate explicitly led incident response and wrote postmortems. - "Led incident response and wrote postmortems; raised availability to 99.94.8%."
**Gaps**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): Oct 2021–Nov 2023 is about 2 years 1 month, and Dec 2023–Oct 2026 is about 2 years 10 months, for roughly 4 years 11 months total, just under 5 years. - "Junior DevOps Engineer, Stratawave Oct 2021 - Nov 2023"
- **Docker in production** (must-have): Docker appears only in the skills list and is not mentioned in any job. - "Linux, Docker, Bash, Jenkins, Kubernetes, AWS, Helm, Prometheus"
- **Infrastructure as code with Terraform** (must-have): The candidate codified environments with Helm, a neighbouring tool, but Terraform is never mentioned. - "Codified environments with Helm, replacing hand-built servers."
- **Linux** (must-have): Linux appears only in the skills list, with no job-level evidence. - "Linux, Docker, Bash, Jenkins, Kubernetes, AWS, Helm, Prometheus"
- **Scripting in Python or Go** (must-have): Only Bash, a neighbouring scripting language, is listed, and it appears only in skills; neither Python nor Go is mentioned. - "Linux, Docker, Bash, Jenkins, Kubernetes, AWS, Helm, Prometheus"
- **Monitoring with Prometheus and Grafana** (must-have): Prometheus appears in skills and alerting work is described, but Grafana is never mentioned. - "Introduced SLOs and alerting that reduced pages per week by 25%."
- **Cloud cost optimisation** (nice-have): Nothing in the resume mentions cloud cost optimisation.
**Round 1 rule checks** (Milestone 2's vocabulary and date arithmetic, shown for comparison; Round 2's judgement above is the one that counts)
- Infrastructure as code with Terraform (has Terraform missing)
- Scripting in Python or Go (has Python missing)
**Improvement suggestions**
- Ask whether Andile has used Terraform or any other infrastructure-as-code tool beyond Helm, for example for provisioning the AWS resources behind the Kubernetes environments at Ironbark Security, and request a concrete example or code sample. If Terraform is truly absent, decide whether the Helm experience is close enough or whether ramp-up on Terraform would be a hiring condition.
- Probe scripting depth in a technical interview: ask for examples of Bash automation they wrote, and whether they have written any Python or Go (such as tooling, Jenkins pipeline helpers or operators). A short take-home or live scripting exercise in Python would settle this gap.
- Verify the monitoring stack behind the SLO and alerting work that cut pages by 25%: confirm how Prometheus was used, and whether dashboards were built in Grafana or another tool. In the same conversation, ask how they used Docker and Linux day to day, since those appear only in the skills list.
- Clarify the experience gap and the cost gap together: the dated roles total about 4 years 11 months against the summary's claim of 5 years, so ask whether any earlier or part-time DevOps work exists. Also ask whether they have done any AWS cost optimisation (rightsizing, reserved instances, cluster autoscaling), as the resume shows none.

### 8. Li Wei (li_wei) - No hire, fit 60
Misses must-have: Linux; Monitoring with Prometheus and Grafana. Resume: `resumes/li_wei.txt`. Round 1 RAG score 80.
**Strengths**
- **Kubernetes in production** (must-have): A Kubernetes platform serving 300+ models at Grab indicates production use. - "Built a Kubeflow and MLflow based model platform on Kubernetes serving 300+ ML models."
- **Docker in production** (must-have): Docker was used for training jobs in the Shopee role. - "Containerised training jobs with Docker; CI/CD for model deployment on GCP."
- **Experience with AWS or GCP** (must-have): GCP was used for model deployment in the Shopee role. - "Containerised training jobs with Docker; CI/CD for model deployment on GCP."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): Built CI/CD for model deployment at Shopee, although the specific tool is not named. - "Containerised training jobs with Docker; CI/CD for model deployment on GCP."
- **Scripting in Python or Go** (must-have): Built a Python SDK in the current role. - "Python SDK for feature store access; Airflow retraining pipelines."
**Gaps**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): Apr 2022–Oct 2026 (~4.6 yrs) + Mar 2020–Mar 2022 (2 yrs) ≈ 6.6 yrs, but it is MLOps/ML platform work, a neighbouring discipline rather than general DevOps, SRE or platform engineering. - "MLOps engineer with 5 years of experience operating ML platforms at scale."
- **Infrastructure as code with Terraform** (must-have): Terraform appears only in the skills list and in no job. - "Python, Kubernetes, Kubeflow, MLflow, Docker, Terraform, AWS, GCP"
- **Linux** (must-have): Linux is not mentioned anywhere in the resume.
- **Monitoring with Prometheus and Grafana** (must-have): Neither Prometheus nor Grafana is mentioned.
- **Incident response and on-call leadership** (nice-have): The resume does not mention incident response or on-call work.
- **Cloud cost optimisation** (nice-have): The resume does not mention cloud cost optimisation.
**Round 1 rule checks** (Milestone 2's vocabulary and date arithmetic, shown for comparison; Round 2's judgement above is the one that counts)
- Linux (has Linux missing)

### 9. Samuel Osei (samuel_osei) - No hire, fit 55
Misses must-have: Docker in production. Resume: `resumes/samuel_osei.md`. Round 1 RAG score 82.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): DevOps Engineer Jul 2019–Jun 2022 (3 years) plus SRE Jul 2022–Oct 2026 (about 4.3 years) is about 7.3 years, which is at least 5. - "Senior Site Reliability Engineer, Ember Analytics Jul 2022 - Present"
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): The candidate built CI/CD pipelines in the current role, and Jenkins is also listed in skills. - "Built CI/CD pipelines with Prometheus that cut deployment time by 18%."
- **Incident response and on-call leadership** (nice-have): The candidate explicitly led incident response in the current SRE role. - "Led incident response and wrote postmortems; raised availability to 99.94.7%."
**Gaps**
- **Kubernetes in production** (must-have): Kubernetes appears only in the summary and skills list, and no job bullet shows production use. - "DevOps engineer with 7 years of experience, most recently working with Kubernetes, AWS, Terraform."
- **Docker in production** (must-have): Docker is not mentioned anywhere in the resume.
- **Infrastructure as code with Terraform** (must-have): Terraform appears only in the summary and skills, and the infrastructure codification bullet names Bash rather than Terraform. - "DevOps engineer with 7 years of experience, most recently working with Kubernetes, AWS, Terraform."
- **Experience with AWS or GCP** (must-have): AWS is claimed in the summary and skills but is not tied to any specific role. - "DevOps engineer with 7 years of experience, most recently working with Kubernetes, AWS, Terraform."
- **Linux** (must-have): Linux appears only in the skills list. - "Linux, AWS, Bash, Jenkins, Kubernetes, Terraform, Prometheus"
- **Scripting in Python or Go** (must-have): Scripting is shown in Bash, a neighbouring language, and there is no Python or Go. - "Codified environments with Bash, replacing hand-built servers."
- **Monitoring with Prometheus and Grafana** (must-have): Prometheus is used in a role, but Grafana is never mentioned. - "Built CI/CD pipelines with Prometheus that cut deployment time by 18%."
- **Cloud cost optimisation** (nice-have): There is no mention of cloud cost optimisation.
**Round 1 rule checks** (Milestone 2's vocabulary and date arithmetic, shown for comparison; Round 2's judgement above is the one that counts)
- Docker in production (has Docker missing)
- Scripting in Python or Go (has Python missing)

### 10. Felix Wagner (felix_wagner) - No hire, fit 55
Misses must-have: Docker in production; Monitoring with Prometheus and Grafana. Resume: `resumes/felix_wagner.docx`. Round 1 RAG score 78.
**Strengths**
- **5+ years of experience in DevOps, SRE or platform engineering** (must-have): Stratawave Apr 2017–Mar 2022 (5 yrs) plus Arclight Apr 2022–Oct 2026 (~4.5 yrs) gives about 9.5 years, which is at least 5. - "DevOps Engineer, Stratawave Apr 2017 - Mar 2022"
- **Infrastructure as code with Terraform** (must-have): He used Terraform for infrastructure as code in his current role. - "Codified environments with Terraform, replacing hand-built servers."
- **CI/CD pipelines (GitHub Actions, Jenkins or similar)** (must-have): He built CI/CD pipelines in both roles. - "Built CI/CD pipelines with CI/CD that cut deployment time by 30%."
- **Incident response and on-call leadership** (nice-have): He led incident response and postmortems in his current SRE role. - "Led incident response and wrote postmortems; raised availability to 99.94.8%."
**Gaps**
- **Kubernetes in production** (must-have): Kubernetes appears only in the skills list and summary, not in any described production role. - "Linux, VMware, Ansible, Bash, Kubernetes, Azure, Terraform, CI/CD"
- **Docker in production** (must-have): Docker is not mentioned anywhere in the resume.
- **Experience with AWS or GCP** (must-have): Only Azure is mentioned, which is a neighbouring cloud rather than AWS or GCP. - "most recently working with Kubernetes, Azure, Terraform."
- **Linux** (must-have): Linux appears only in the skills list and not in any job description. - "Linux, VMware, Ansible, Bash, Kubernetes, Azure, Terraform, CI/CD"
- **Scripting in Python or Go** (must-have): He shows Bash scripting, a neighbouring language, but not Python or Go. - "Built CI/CD pipelines with Bash that cut deployment time by 40%."
- **Monitoring with Prometheus and Grafana** (must-have): Neither Prometheus nor Grafana is mentioned.
- **Cloud cost optimisation** (nice-have): The resume does not mention any cloud cost optimisation.
**Round 1 rule checks** (Milestone 2's vocabulary and date arithmetic, shown for comparison; Round 2's judgement above is the one that counts)
- Docker in production (has Docker missing)
- Experience with AWS or GCP (has AWS missing)
- Scripting in Python or Go (has Python missing)

## How to read this report
- **Round 1** ranked every resume with Milestone 2's hybrid search (embeddings, BM25, skill match) and kept the top 10; on a re-screen the previous shortlist is carried forward too, so nobody leaves the list because the search changed. Nobody is rejected at this stage.
- **Round 2**: Claude judged each requirement as met, partial or missing, quoting the resume. Fit = weighted share met (must-have x2, nice-to-have x1; partial = half). A 'met' whose quote is not in the resume counts as partial.
- **Round 3**: Hire = every must-have met; No hire = a must-have missing; Borderline = in between.
- These are screening recommendations for a human decision-maker, not hiring decisions.
