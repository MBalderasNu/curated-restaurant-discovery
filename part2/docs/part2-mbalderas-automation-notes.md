The script labels each recommendation using a set of practical quality rules based on WoM guidelines plus my curation preferences.

First, it removes content that clearly does not fit WoM.
It removes recommendations for chains and franchises (for example Hesburger or McDonald’s style venues).
It removes hotel entries because hotels are not the target type in this dataset.
It removes empty or near empty comments because they do not help a member.
It removes non English recommendations since the guideline is to write in English.
It removes negative recommendations (warnings, “avoid this”, etc.) because WoM states negative recommendations get deleted.
It removes recommendations that read like marketing copy or AI generated content, especially when they are overly polished, impersonal, and not grounded in real food or experience details.

Second, it flags recommendations that might be valuable but need improvement.
If a recommendation uses too many emojis, it is flagged as Recommendation needs editing, and in stricter cases can be removed when paired with hype or templated language.
If a recommendation uses dash heavy formatting instead of natural writing, it is flagged as Recommendation needs editing or Needs more information depending on how specific the content is.
If the writing is messy (excess punctuation or overly chaotic formatting) but still contains good specifics, it is flagged as Recommendation needs editing.
If a recommendation is overly positive without enough real specifics, it is flagged as Needs more information or removed if it is extremely short and hype only.

Third, it handles weak signal cases.
If there is no image, the text needs to carry more weight. Short vague comments without specifics get flagged as Needs more information.
If the text is below the WoM minimum length and does not contain strong specifics, it is removed as low signal.
If the comment is short and lacks specificity, it is flagged as Needs more information.

Finally, it keeps recommendations that read like a real friend to friend recommendation.
If the text includes concrete details such as what to order, what makes the place special, and what the experience is like, it is labeled Keep.

How to run
From the project root, install dependencies and run the script.

pip install -r requirements.txt
python part2\src\label_recommendations.py

Input
The script reads the first .xlsx file found in part2/input and expects the following columns: Restaurant → Name, Comment, Image yes/no, Created At, Tags. Tags are intentionally not used for decision-making in this version.

Output
The script writes a labeled CSV file to part2/output/recommendations_labeled.csv. It includes the original fields plus Predicted decision, Confidence, and Reason codes.

Output fields
The output CSV adds three fields that explain both the decision and why it happened.

Predicted decision
This is the automated label assigned to each recommendation. The script uses four categories.
Keep means the recommendation is specific, helpful, and reads like a genuine friend to friend suggestion.
Remove means it breaks core WoM guidelines or undermines trust, for example chains, hotels, non English, negative recommendations, empty or generic comments, or AI or marketing style content.
Needs more information means the recommendation might be valid, but the text does not provide enough useful detail to confidently keep it.
Recommendation needs editing means the content is valuable but needs cleanup, for example formatting issues, emoji overuse, spelling issues, or overly messy writing.

Reason codes
Reason codes explain which rule triggered the decision. For this assignment, each recommendation is assigned one reason code to limit scope and keep the output easy to review. In a production version, this could be extended to support multiple reason codes per recommendation when multiple signals apply.
Examples include chain_or_franchise, hotel_not_target, non_english_comment, negative_recommendation, dashy_formatting, too_many_emojis, hype_plus_format_spam, low_specificity, no_image_weak_text, and spelling_issues.

Confidence
Confidence is a simple indicator of how certain the script is about the decision.
High is used for clear cut cases where the rules strongly apply, for example chain or franchise, non English, negative recommendation, empty or generic comments, or strong AI hype patterns.
Medium is used for borderline cases where the recommendation may still be useful but needs improvement or more context, such as low specificity, no image plus weak text, formatting issues, or spelling related edits.