"""
Warren David McDonald's Professional Resume & Knowledge Base
Structured authentic context for the Gemini AI Resume Agent.
"""

WARREN_RESUME = """
# Warren David McDonald - AI DevSecOps Engineer

**Domain:** https://warrenmac.com  
**LinkedIn:** https://www.linkedin.com/in/warren-david-mcdonald/  
**Resume PDF:** /warren-mcdonald-resume.pdf  
**Email:** wmickeyd@gmail.com  
**Phone:** +1 (973) 590-6725  
**Location:** Harrison, NJ  
**Role:** AI DevSecOps Engineer | Kubernetes, Cloud & Infrastructure Platform Specialist  

---

## Professional Summary
Forward-thinking AI DevSecOps and Platform Engineer with over 10 years of experience orchestrating resilient cloud infrastructure, architecting highly available Kubernetes clusters, automating CI/CD pipelines, and integrating AI/ML workflows into enterprise systems. Proven track record leading infrastructure transformations across AWS, Azure, and Google Cloud (GCP), enforcing Zero-Trust security and SOC 2 compliance, and building defense-in-depth guardrails for generative AI and agentic systems.

---

## Chronological Work Experience

### 1. Interwell Health LLC (Remote)
**Role:** Lead DevOps Engineer  
**Dates:** August 2022 - January 2026 (Last / Most Recent Place of Employment)  
**Key Contributions & Achievements:**
- Led comprehensive DevOps transformation, orchestrating cloud infrastructure, Dockerizing applications, and implementing modern CI/CD pipelines in GitHub Actions (migrating legacy pipelines from Jenkins) for front-end, back-end, and DevOps tooling.
- Architected and maintained highly available AWS Kubernetes (EKS) clusters and managed 100+ Route53 domains, ensuring seamless infrastructure deployment for enterprise operations.
- Drove AWS to Azure cloud migration utilizing Terraform, significantly reducing annual cloud infrastructure spend.
- Led the design, deployment, and implementation of Databricks in Azure via Terraform, enabling data engineering teams to leverage AI and machine learning for improved patient outcomes.
- Spearheaded cross-functional teams to implement Infrastructure as Code (IaC), containerization, and automated testing, establishing SOC 2 compliant disaster recovery protocols.
- Provided 24/7 on-call incident response and troubleshooting for production healthcare applications.

### 2. Workpath (Remote)
**Role:** Senior DevOps Engineer  
**Dates:** October 2021 - June 2022  
**Key Contributions & Achievements:**
- Built cloud infrastructure and deployed production applications in AWS using Terraform.
- Managed Kubernetes, AWS Fargate, and EC2 compute environments.
- Migrated VPN infrastructure to Pritunl AMI, codified configurations in Terraform, and configured VPC peering across environments.
- Automated creation of staging and test environments using BASH and Golang automation scripts.
- Transitioned DNS management from AWS Route53 to Cloudflare.
- Migrated CI/CD workflows from AWS CodePipeline and GitHub Actions to CircleCI for improved deployment visibility.
- Architected cross-region read-replica RDS clusters for high database resiliency.
- Implemented full-stack observability and monitoring dashboards using Prometheus and Grafana.

### 3. Synchrony (Remote)
**Role:** Assistant Vice President (AVP), Senior DevOps Engineer  
**Dates:** July 2018 - October 2021  
**Key Contributions & Achievements:**
- Managed deployment infrastructure using Chef/OpsWorks in AWS and oversaw SDLC release pipelines for web and mobile platforms.
- Built, monitored, and maintained production, staging, and development environments.
- Developed Python deployment automation leveraging AWS APIs to deploy services via Jenkins.
- Implemented autoscaling policies that reduced service timeouts by 90% during peak traffic spikes.
- Authored comprehensive infrastructure documentation to accelerate developer onboarding.
- Built security-hardened AMIs using HashiCorp Packer and Jenkins with Docker pre-installed.
- Mentored and managed offshore engineering teams and conducted continuous code reviews.

### 4. New York Media (New York, NY)
**Role:** DevOps Engineer  
**Dates:** May 2017 - May 2018  
**Key Contributions & Achievements:**
- Managed and streamlined CI/CD pipelines, transitioning engineering teams to CircleCI and troubleshooting container builds.
- Deployed Node.js CMS with PostgreSQL backend using AWS CodeDeploy scripts and BASH automation.
- Configured Apache and Nginx web server rewrites for high-traffic media properties and optimized CDN performance using Fastly VCL.
- Built and maintained centralized ELK (Elasticsearch, Logstash, Kibana) logging stack for developer observability.

### 5. Kenzan Media (New York, NY)
**Role:** DevOps Engineer  
**Dates:** April 2016 - April 2017  
**Key Contributions & Achievements:**
- Maintained AWS environments, building and deploying AMIs via Bamboo and Ansible.
- Wrote Terraform scripts to codify AWS cloud infrastructure.
- Developed Python scripts for data processing and unhexing Aegisthus data in AWS.
- Researched and deployed open-source observability solutions including Graylog and Netflix OSS tooling.

### 6. Comcast (Philadelphia, PA)
**Role:** DevOps Engineer  
**Dates:** March 2014 - March 2016  
**Key Contributions & Achievements:**
- Built and deployed over a dozen Java-based services in Tomcat and Jetty application servers with centralized logging in Splunk.
- Performed Blue/Green (Canary) deployments using Puppet for enterprise back-office (XBO) systems and administered Apache Cassandra distributed databases.
- Created JRuby RESTful API and frontend scanner for Java applications via JMX.
- Assisted engineering transition and migration from SVN to Git.

---

## Education & Certifications
- **Education:** New Jersey Institute of Technology (NJIT) — Bachelor of Science (B.S.) in Information Technology (September 2007 - December 2012, Newark, NJ)
- **Certification:** AWS Certified Developer - Associate (April 2021 - April 2024, Verification ID: F2B4829BC24E13GF)

---

## Featured AI & DevSecOps Projects

### 1. Fortified AI Resume Platform (warrenmac.com)
- Interactive portfolio and LLM assistant running on Kubernetes (OrbStack & GCP GKE).
- Defense-in-depth AI DevSecOps guardrail pipeline: Ingress prompt injection detection, cryptographic canary tokens preventing system prompt exfiltration, egress PII/secret scrubbing, and token rate-limiting.
- Restricted Pod Security Standards (non-root UID 10001, immutable read-only rootfs) and Zero-Trust NetworkPolicies restricting outbound traffic strictly to LLM APIs.

### 2. Autonomous AI Agent Development & MCP Tool Orchestration
- Engineered an autonomous AI agent leveraging local LLMs, Model Context Protocol (MCP) servers, and function calling to automate research and Kubernetes operations.
- Integrated custom tools with a ReAct (Reasoning + Acting) loop for multi-step task execution.

### 3. Azure Databricks AI/ML Platform at Interwell Health
- Designed and deployed enterprise Databricks infrastructure in Azure using Terraform, enabling data science and ML teams to run predictive healthcare analytics.
"""
