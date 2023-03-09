# Twitter-SNA
Twitter SNA queries the Twitter API Recent Search endpoint for tweet data,
automates the cleaning/structuring of that data and outputs it to a .csv file.
Optionally, you may output nodes and edges lists for between-user interactions
and hashtag usage. For the latter an edge is created whenever two hashtags co-occur within a tweet.

In order to use Twitter SNA, you will need to have acquired a Twitter API key and entered it into the script at the location shown below:

<img width="635" alt="Screenshot 2023-03-09 at 5 05 56 PM" src="https://user-images.githubusercontent.com/110642777/224049503-a536131d-3017-42fc-bac9-c4fd20fc6592.png">

Options:

	--help: display this help menu;
  
	--sna: output nodes and edges lists for interactions between users.
	       Note that this will only execute once the scraping has completed;
         
	--json: output .json file;
  
	--tags: output nodes and edges lists for users and hashtags. Note that
	        this will only execute once scraping has been completed.

Twitter search operators that have been confirmed to work with Essential API
access include:

	--@: Matches any Tweet that mentions the given username.
  
	--from:: Matches any Tweet from a specific user.
  
	--is:retweet: Deliver only explicit Retweets that match a rule.
  
	--has:hashtags: Matches Tweets that contain at least one hashtag.

Please see Twitter API documentation for additional information on usage and
available operators.
