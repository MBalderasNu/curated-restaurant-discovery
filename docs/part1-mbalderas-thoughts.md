Part 1: New Openings

For this assignment, I decided to use Wolt’s list of new restaurants in Helsinki. Typically, bigger franchises appear first (like McDonald’s, Subway, Hesburger, etc.), which led me to define a blocklist.txt, because not every restaurant fits the vision of what WoM represents.

I started with a web scraping approach to grab restaurant names from the page, followed by trying to retrieve venue details such as address and possible tags.

At first, I wasn’t able to scrape the location details accurately, so I decided to create a Google Cloud Console account. This allowed me to access the Places API, which I used to map restaurants to correct address details, followed by tags.

Initially, I pulled in tags into the CSV file that weren’t needed, so I created a separate tag list that filters which tags should be stored in the CSV.

At this point, I had a list of restaurants that followed my tag criteria and also followed my blocklist.

Since the goal is to find new restaurants, I added a filter where I only kept restaurants with less than 100 Google reviews. The idea is that fewer reviews could mean the place hasn’t existed long enough to accumulate reviews. The number isn’t final and could change depending on the city in the future.

There’s also no reliable way to target exact opening dates using these data sources, so this pipeline is designed to generate high-signal candidates rather than guaranteed “opened in the last 6 months” results. Over time, the blocklist.txt can be edited and refined, which should improve the precision of what gets returned.

The script outputs a CSV containing restaurant name, full address, restaurant description, and curated tags.