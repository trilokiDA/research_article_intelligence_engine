summarization_prompt = """
You are an expert in analysing scientific reasearch paper. Analyze the data below in <article> xml tags, which is a title, journal, date, abstract and afiliations of some scientific article.
Your task is to provide the following details:
* Title - Title of the scientific article as given
* Journal - Journal in which the article is published as given
* Date - Publication date of the article as given in yyyy-mm-dd format
* Abstract - Abstract text of the article as given
* Entity - List of topic entities extracted from the article. **You MUST select ONLY from these exact values (case-sensitive):**
  - 'electronic cigarettes', 'nicotine', 'smoking cessation', 'cigarettes', 'youth', 'vaping', 'smoking', 'snus', 'tobacco products', 'smokeless tobacco', 'public health', 'tobacco', 'cigars', 'harm reduction', 'iqos', 'hookah', 'dual use', 'heated tobacco products', 'quitting', 'e-liquids', 'population assessment of tobacco and health study', 'nicotine replacement therapy', 'asthma', 'marijuana', 'social media', 'addiction', 'juul', 'cytotoxicity', 'former smokers', 'current smokers', 'gender', 'mental health', 'tobacco control policies', 'health risks', 'smoking reduction', 'secondhand smoke', 'cancer', 'depression', 'FDA', 'alcohol', 'harm perceptions', 'chemicals', 'nicotine pouches', 'smoking status', 'advertising', 'gender differences', 'smoking initiation', 'cardiovascular disease', 'electronic nicotine delivery systems (ENDS)', 'others'
  **Choose a diverse and representative set (typically 3-5) that best cover the abstract. If nothing matches well, use 'others'.**
* Subject - Broad subject of the research article. **Select ONLY from:** 'Heated Tobacco Products (HTP)', 'E-cigarettes', 'Vaping', 'Oral Smokeless', 'Other'
* Summary - A concise, plain-language summary of the article, suitable for leadership review
* Category - Broad research category of the research article. **Select ONLY from:** 'Aerosol Chemistry', 'Preclinical Studies', 'Clinical Studies', 'Behavior Studies', 'Epidemiology', 'Case Studies', 'Economic Studies', 'Public Health Studies', 'Other'
* Country - Full country name of study, or 'n/a' if not specified
* Sentiment - Sentiment towards Tobacco Harm Reduction (THR) expressed in the article. **Select ONLY from:** 'Positive', 'Negative', 'Neutral', 'Mixed', 'Undefined'
* Industry affiliation - Industry affiliation (e.g., PMI, JTI, BAT) if mentioned, 'n/a' if not provided

<article>
<Publication ID>{doc_id}</Publication ID>
<title>{title}</title>
<journal>{journal}</journal>
<date>{date}</date>
<abstract>{abstract}</abstract>
</article>

**Language Guidelines for Summary Field**:
When writing the Summary, you MUST use people-first language that emphasizes the person before their condition, behavior, or characteristic:

Required patterns:
* Write "participants who smoke" NOT "smokers"
* Write "individuals with asthma" NOT "asthmatics" or "asthmatic individuals"
* Write "people who use tobacco" NOT "tobacco users"
* Write "participants with diabetes" NOT "diabetics" or "diabetic participants"
* Write "individuals with disabilities" NOT "disabled individuals"
* Write "people who vape" NOT "vapers"
* Write "participants who smoke and have asthma" NOT "asthmatic smokers"

General principle: Always describe people by stating who they are first (participants, individuals, people) followed by what they do or have (who smoke, with asthma), rather than defining them by a single characteristic.

**Note**
* **CRITICAL:** You MUST use the exact entity/subject/category/sentiment values listed above. Do NOT create variations or synonyms (e.g., use 'marijuana' NOT 'cannabis', use 'electronic cigarettes' NOT 'e-cigarettes'). When in doubt, use 'others' for entities, 'Other' for subject/category, or 'Undefined' for sentiment.
* If the <abstract> field is null, empty, or missing:
    * Set "summary" to an empty string "".
    * Infer "subject" from the article title using the Subject values listed above.
    * Infer "category" from the article title using the Category values listed above.
    * Extract entities from the title instead of the abstract.
    * **Do NOT guess additional information beyond what the title directly implies.**
"""

summary_evaluation_prompt = """
You are an expert verifying the factual accuracy of the claims in generated summary.
Below is the original abstract (in <article> xml tags) from a research article and claims in a list format(in <claims> xml tag) from the generated summary.

<article>
{article}
</article>

<claims>
{claims}
</claims>

Categorize each claim under one of the following label:
* Supported : The claim is explicitly or clearly implied in the article.
* Contradicted : The claim states the opposite meaning or evidence.
* Not mentioned : The claim cannot be confirmed from the article or adds new unsupported facts.

Provide a breif explaination for each of the label selected.
"""

revalidate_prompt = """
Please try again and **ensure the schema is properly followed** as you have failed with the following validation error {error_json} \n
"""

reinfer_prompt = """
Below is evaluation feedback from an automated factual consistency checker applied to a previous summary on a similar task. Use it to improve accuracy.

Evaluation behavior:
- Each summary sentence is evaluated independently.
- Claims must be explicitly supported by the article.
- Adding unstated context or applications results in "Not mentioned" or "Contradicted".

Below is the abstract that was summarized:
{abstract}

Summary:
{summary}

Evaluation results:
{claims}

Generate a summary such that every individual sentence can be directly verified against the article text without inference.
"""

quality_scoring_prompt = """
You are an expert evaluating the quality of a generated research article summary.

Original Article:
<article>
<title>{title}</title>
<abstract>{abstract}</abstract>
</article>

Generated Summary:
{summary}

Generated Analysis:
- Entities: {entities}
- Subject: {subject}
- Category: {category}
- Sentiment: {sentiment}

Evaluate the summary quality on a 0-100 scale across these dimensions:

1. **Factual Accuracy (40% weight):**
   - Are all claims directly supported by the abstract?
   - No hallucinations or unsupported inferences?
   - No contradictions with source material?
   Score: 0 (many errors) to 100 (perfect accuracy)

2. **Completeness (30% weight):**
   - Does it cover the key findings/conclusions?
   - Are important details preserved?
   - Is the scope appropriate (not too brief or verbose)?
   Score: 0 (missing key points) to 100 (comprehensive)

3. **Clarity (20% weight):**
   - Is the language clear and concise?
   - Is it readable for leadership (non-technical audience)?
   - Is the structure logical?
   Score: 0 (unclear) to 100 (very clear)

4. **People-First Language (10% weight):**
   - Uses "people who smoke" NOT "smokers"
   - Uses "individuals with asthma" NOT "asthmatics"
   - Uses "participants who vape" NOT "vapers"
   - Consistently applies people-first principles?
   Score: 0 (many violations) to 100 (perfect adherence)

Calculate:
- Overall Score = (Factual Accuracy × 0.4) + (Completeness × 0.3) + (Clarity × 0.2) + (People-First × 0.1)

Provide scores and brief justifications.
"""

hallucination_detection_prompt = """
You are a fact-checker identifying unsupported or hallucinated claims in a generated summary.

Original Abstract:
{abstract}

Generated Summary:
{summary}

Your task:
1. Break the summary into individual factual claims
2. For each claim, check if it is:
   - **Supported:** Directly stated or clearly implied in the abstract
   - **Not Mentioned:** Adds information not present in the abstract
   - **Contradicted:** States the opposite of what the abstract says

3. Flag any claims that are "Not Mentioned" or "Contradicted" as potential hallucinations

Return:
- hallucination_detected: true/false
- hallucination_examples: List of unsupported claims (empty if none)

Be strict: If a claim cannot be directly verified from the abstract text, mark it as unsupported.
"""

people_first_check_prompt = """
You are checking adherence to people-first language guidelines.

Generated Summary:
{summary}

People-First Language Rules:
CORRECT: "people who smoke", "individuals with asthma", "participants who vape"
INCORRECT: "smokers", "asthmatics", "vapers"

General pattern:
CORRECT: "[people/individuals/participants] who [action/condition]"
INCORRECT: "[condition]-er" or "[condition] people"

Task:
1. Scan the summary for any violations of people-first language
2. List each violation with the incorrect phrase and suggested correction
3. Return:
   - people_first_violations: List of violations (empty if none)
   - people_first_score: 0-100 (100 = no violations, deduct 20 per violation)

Examples of violations:
- "smokers" should be "people who smoke"
- "diabetics" should be "individuals with diabetes"
- "asthmatic smokers" should be "participants who smoke and have asthma"
"""

entity_consistency_check_prompt = """
You are verifying that extracted entities match the article content.

Original Abstract:
{abstract}

Extracted Entities:
{entities}

Task:
1. Check if each extracted entity is actually mentioned or clearly implied in the abstract
2. Identify any entities that are:
   - **Incorrect:** Not present in the abstract
   - **Missed:** Important topics present but not extracted
3. Return:
   - entity_consistency: true/false (false if major issues)
   - entity_issues: List of problems (empty if none)

Be reasonable: Minor omissions are acceptable, but major topics should be captured.
"""
