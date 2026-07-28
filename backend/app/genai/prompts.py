summarization_prompt = """
You are an expert in analysing scientific reasearch paper. Analyze the data below in <article> xml tags, which is a title, journal, date, abstract and afiliations of some scientific article.
Your task is to provide the following details:
* Title - Title of the scientific article as given
* Journal - Journal in which the article is published as given
* Date - Publication date of the article as given in yyyy-mm-dd format
* Abstract - Abstract text of the article as given
* Entity - List of topic entities extracted from the article. **Select only from the Entity values specified. Choose a diverse and representative set of options that best cover the abstract. If not then mark it as others**
* Subject - Broad subject of the reasearch article
* Summary - A concise, plain-language summary of the article, suitable for leadership review
* Category - Broad research category of the research article
* Country - Full country name of study, or 'n/a' if not specified
* Sentiment - Sentiment towards Tobacco Harm Reduction (THR) expressed in the article
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
* Please only select Entity from EntityEnum and Category from CategoryEnum and double check your findings.
* If the <abstract> field is null, empty, or missing:
    * Set "summary" to an empty string "".
    * Infer "subject" from the article title using the SubjectEnum categories.
    * Infer "category" from the article title using the CategoryEnum categories.
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
