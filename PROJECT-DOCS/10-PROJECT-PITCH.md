# Project Pitch — Lease Origination Sample Application (SIGNiX Integration)

*This document is written as the pitch that would have been presented to secure sponsorship and stakeholder approval for the project. It states why we are doing the project, who it serves, and what benefits we expect.*

---

## 1. Executive Summary

We propose building a **lease origination sample application** that integrates with **SIGNiX** for electronic document signing. The application will serve as a **reference implementation** for SIGNiX integration, a **demonstrable product** for sales, a **teaching vehicle** for AI-powered application development, and a **reusable template** for document-centric business applications in other domains (wealth management onboarding, loans, equipment leasing, health installment plans, etc.). Success will strengthen SIGNiX’s position as the integration choice for document signature automation, educate internal and external developers, and establish a repeatable, documented approach to building such applications with AI-powered code generation.

---

## 2. Why This Project?

### 2.1 Business need

- **SIGNiX** needs a **representative, real-world-style application** that integrates with its APIs so that prospects, customers, and third-party developers can see exactly how an end-to-end integration works: data collection, document templating, document generation, submission to SIGNiX, and synchronization with SIGNiX through a dashboard as signing progresses.
- **Sales and presales** need an **impressive, credible demo**—not a toy—that can be shown in a sales process. The application must be recognizable to a third-party developer as the kind of application they would build, so that the integration story is clear and trustworthy.
- **Developer education** requires a **sample application and reference implementation** that customer developers can study and adapt. Content derived from this project (tutorials, blog posts, documentation) will support their learning and will be used to **promote integration with SIGNiX**—so that SIGNiX appears prominently in search results and is recommended or chosen by AI-powered systems (e.g. chatbots, AI-powered development environments like Cursor) when users ask how to add signature process integration to an existing app.
- **Internal teams** (SIGNiX and Future Capital) need to **learn and standardize** how to use **AI-powered code generation** (“vibe coding”) in an effective, efficient, and disciplined way. This project will produce not only an application but **documentation and a template** that teach others how to build and extend applications without writing code by hand, while ensuring the application does exactly what is required.
- **Future projects** that are document-centric (wealth management onboarding, vehicle or equipment leases, personal or commercial loans, health installment plans) need a **proven starting point**. This project will deliver a template and documentation so that creating a new application for a different but similar use case becomes quick and easy—e.g. “using this project as a template, make a project like this, but for personal loans.”

### 2.2 Strategic value

- **Prove the power of current AI-powered code generation** by delivering an application that represents real-world needs and showcases SIGNiX integration end-to-end.
- **Clarify end-to-end usage** of an application that integrates with SIGNiX: data collection, templating, document generation, submission to SIGNiX, and synchronization with SIGNiX through a dashboard (status updates, signer progress, download of signed documents and artifacts).
- **Establish best practices** for application development when using AI-assisted development: clear requirements, scope, approach, and a Knowledge → Design → Plan documentation structure so that the application can be recreated, extended, or reused as a template.

### 2.3 Design goals: explicit patterns, separate from business logic

A key goal of this project is to **make explicit** a set of patterns that are often muddled with business logic in document-centric applications. When these patterns are buried in domain-specific code, the result is hard to maintain and hard for developers in a *different* business domain to learn from or empathize with. This project keeps them explicit and separate:

1. **Data-to-template mapping** — How data in the application is mapped to templates (e.g. schema paths → template variables) is a clear, documented layer—not ad-hoc code scattered in business logic.
2. **Templates used to generate documents** — How templates are used to generate documents (template + data → rendered output → PDF) is a defined flow, separable from lease-specific or domain-specific logic.
3. **Configurable text tagging** — Text tagging (e.g. signature fields, date-signed fields for SIGNiX) is **configured** (e.g. in tagging_data), not hardcoded. No logic that encodes specific knowledge about the data or template structure is required to add or change which fields are signature fields or which signer slot they use.
4. **Deals and document set templates** — How deals are set up according to document template sets is explicit: deal type → document set template → ordered list of templates. Which documents apply to a deal is determined by configuration (deal type and its associated document set template), not by hardcoded business logic.
5. **Documents as instances with versions** — Documents are modeled as **instances with versions** (e.g. DocumentInstance, DocumentInstanceVersion with draft, submitted, final). This general pattern is explicit so that regeneration, “as sent” vs “signed,” and audit are clear—not one-off handling of “this PDF we generated.”
6. **General SIGNiX interface** — The integration with SIGNiX (build payload, send, parse response, push handling, download) is a **general interface** that is not bundled with business logic. A developer building a personal-loan or wealth-management application can reuse or adapt the SIGNiX integration pattern without wading through lease-officer or jet-pack-specific code.

By keeping these six patterns explicit and separate from the leasing domain, the application stays maintainable and becomes a **learnable reference** for developers in any document-centric domain.

---

## 3. Who This Serves (Stakeholders and “Customers”)

The project has **multiple stakeholders**; satisfying them is how we define success.

### 3.1 Project lead

The **project lead** is a primary stakeholder. The project lead is responsible for direction, technical research, best practices, and ensuring the application and documentation serve the goals below. Their needs include:

- **Learning** how to work with an AI-powered code-generating system (e.g. Cursor) to effectively build, maintain, and extend applications without personally writing code, while ensuring the application does exactly what is needed.
- **Creating documentation and a template** for this kind of work so that others can be taught to do it.
- **Proving out** the power of current AI-powered code generation by producing an impressive application that represents real-world applications and showcases SIGNiX integration.
- **Clarifying** end-to-end usage of an application that integrates with SIGNiX (data → templates → generation → submit → dashboard/sync).
- **Ensuring** the application is a clear and accurate representative of the sort of application that integrates with SIGNiX, so that a third-party developer would recognize it and have a clearer understanding of the integration process.

### 3.2 Engineering staff (SIGNiX and Future Capital)

- **SIGNiX software engineering** will use this project to learn how SIGNiX APIs are used in real-world integrations and how AI-powered code generation will be used by customers to build those integrations. They will see what support they can provide to third-party developers to make integration easier, faster, and more effective.
- **Future Capital engineering** will focus on learning the AI-powered code generation process and will also learn about SIGNiX, which will help when integrating document signature processes into the Future Capital platform.

### 3.3 Other technically-savvy staff (SIGNiX and Future Capital)

- **Marketing** (with AI and some coding background), **SIGNiX integrations support analyst** (supporting third-party developers), and **SIGNiX Sales Engineer** (technical enough to administer HubSpot, write low-code integrations with Zapier, Slack, Airtable, etc.) are stakeholders. The application and related content will support demos, support discussions, and technical marketing.

### 3.4 SIGNiX prospects, customers, and their developers

- **Prospects and customers in a sales process**: The app will be used by SIGNiX sales to demonstrate a representative business application integrated with SIGNiX.
- **Developers building customer integrations**: The app will serve as a **sample application / reference implementation**. The app and content from this project (tutorials, blog posts, etc.) will be used for their education. That content will promote integration with SIGNiX so that SIGNiX appears prominently in search and is recommended or chosen by AI-powered systems when users ask how to add signature process integration to an application.

### 3.5 End users in the scenario

In the **usage scenario**, the primary user is a **lease officer** (employee). The second signer is a **lessee** (customer/contact). In practice, the app will be used primarily by SIGNiX staff demonstrating the integration or by developers learning how to integrate with SIGNiX—playing the roles of lease officer, lessee, and system administrator (configuring templates, etc.). The application must focus on the **leasing use case** so that the scenario is clear, even though the broader intent includes marketing SIGNiX, teaching AI-powered code generation, and providing a template for other document-centric applications.

---

## 4. Expected Benefits

- **SIGNiX**: A credible, demonstrable reference integration; clearer support and sales materials; stronger visibility in search and AI recommendations for signature integration.
- **Future Capital**: A repeatable, documented approach to building document-centric applications with AI-assisted development; familiarity with SIGNiX for future platform integration.
- **Project lead**: Proven ability to drive an application to completion using AI-powered code generation; reusable documentation and template for teaching and for future projects.
- **Third-party developers**: A recognizable sample application, clear integration path, and educational content that reduce the effort and risk of integrating with SIGNiX.
- **Future projects**: A template and documentation that make it quick and easy to create new applications for different but similar document-centric use cases (e.g. personal loans, wealth management onboarding).

---

## 5. Success Criteria (High Level)

- The application can be **recreated from scratch** by following the project’s documentation and plans.
- The application **demonstrates end-to-end SIGNiX integration** (data → documents → submit → signing → dashboard/sync → download of signed documents and artifacts).
- **Third-party developers** recognize the application as a realistic example of an application that integrates with SIGNiX and can use it (and derived content) to understand and implement integrations.
- **Internal engineering and technical staff** can use the project to learn AI-powered code generation and SIGNiX integration in a disciplined, repeatable way.
- The **documentation and structure** support using the project as a **template** for other document-centric applications (e.g. “like this, but for personal loans”).

---

*For system-level requirements derived from this pitch, see **40-REQUIREMENTS.md**. For what is in or out of scope for this version, see **30-SCOPE.md**. For how we build and document the project, see **20-APPROACH.md**. For work-breakdown and level of effort, see **50-WBS.md** and **60-LOE.md**.*
