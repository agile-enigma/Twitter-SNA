import requests, os, json, csv, re, sys, getopt
from pprint import pprint
from datetime import datetime

#Set arguments
argumentList = sys.argv[1:]
options = "sjht"
long_options = ["sna", "json", "help", "tags"]
arguments, values = getopt.getopt(argumentList, options, long_options)

for currentArgument, currentValue in arguments:
    if currentArgument in ('--help'):
        print('\nThis script queries the Twitter API Recent Search endpoint \
for tweet data,\nautomates the cleaning/structuring of that data and outputs it to a .csv file.\n\
Optionally, you may output nodes and edges lists for between-user interactions\n\
and hashtag usage.\n\nOptions:\n\t--help: display this help menu;\n\t--sna: output nodes and edges \
lists for interactions between users.\n\t       Note that this will only execute once the scraping has completed\
;\n\t--json: output .json file;\n\t--tags: \
output nodes and edges lists for users and hashtags. Note that\n\t        this will only execute \
once scraping has been completed.\
\n\nTwitter search operators that have been confirmed to work with Essential API\naccess include:\n\t\
--@: Matches any Tweet that mentions the given username.\n\t--from:: Matches any \
Tweet from a specific user.\n\t--is:retweet: Deliver only explicit Retweets that match a rule\n\t\
--has:hashtags: Matches Tweets that contain at least one hashtag.\n\nPlease see \
Twitter API documentation for additional information on usage and\navailable operators.\n')
        quit()

#set variables
now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# To set your environment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ.get("BEARER_TOKEN")
base_url = "https://api.twitter.com/2/tweets/search/recent?"
tweet_fields = "&tweet.fields=author_id,public_metrics,\
created_at,entities,lang,referenced_tweets,in_reply_to_user_id"
user_fields = "&user.fields=username,entities"
expansions = "&expansions=author_id,entities.mentions.username,\
referenced_tweets.id,referenced_tweets.id.author_id,in_reply_to_user_id"

#Optional params: start_time,end_time,since_id,until_id,max_results,next_token,
#expansions,tweet.fields,media.fields,poll.fields,place.fields,user.fields
#query_params = {'query':'','tweet.fields':''}
query = input('Please enter your Twitter query: ')
while True:
    if query != "":
        break
    else:
        continue
query_url = base_url + 'query=' + query + tweet_fields + user_fields + expansions + "&max_results=100"
next_page_url = ""
next_json_response = ""
page_iteration = 1
sna_edges_list = []
sna_nodes_list = []
hashtag_edges_list = []
hashtag_nodes_list = []

#authenticate to Twitter API
def bearer_oauth(r):
    #Method required by bearer token authentication.
    r.headers["Authorization"] = f"Bearer [API KEY HERE NO BRACKETS]"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r
#connect to Twitter API recent search endpoint
def connect_to_endpoint(url):
    response = requests.get(url, auth=bearer_oauth)
    #print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response

directory_name = "twitter-recent_" + query + "_" + now
os.mkdir(directory_name)
os.chdir(directory_name)

def main():
    json_response = connect_to_endpoint(query_url)
    print('...acquiring data...')
    tweets = json.loads(json_response.text)
    pprint(tweets)

    #create .csv file
    with open(str(query) + ": twitter_recent " + now + ".csv", "w", encoding='utf-8') as csv_file:
        #convert .csv file to csv_writer object
        csv_writer = csv.writer(csv_file)
        #create .csv column headers
        csv_writer.writerow(["author_id",
                             "author_handle",
                             "author_name",
                             "tweet_id",
                             "tweet_url",
                             "created_at",
                             "date",
                             "time",
                             "language",
                             "text",
                             "tweet_type",
                             "referenced_handle",
                             "mentioned_handles",
                             "hashtags",
                             "image_links",
                             "external_url",
                             "url_host",
                             "article_title",
                             "article_description",
                             "retweet_count",
                             "reply_count",
                             "like_count",
                             "quote_count"
                             ])

        has_another_page = True
        while has_another_page:
            if tweets.get("data") is not None:
                for i in range(tweets["meta"]["result_count"]):
                    for object in tweets["includes"]["users"]:
                        if object["id"] == tweets["data"][i]["author_id"]:
                            author_id = object["id"]
                        if object["id"] == tweets["data"][i]["author_id"]:
                            author_handle = object['username']
                        if object["id"] == tweets["data"][i]["author_id"]:
                            author_name = object["name"]
                        else:
                            continue
                    #append author id, handle and name
                    tweet_data_row = [
                                    author_id,
                                    author_handle,
                                    author_name
                                    ]

                    sna_nodes_list.append([author_handle, author_handle])
                    hashtag_nodes_list.append([author_handle, author_handle])

                    #append tweet id
                    tweet_data_row.append(tweets["data"][i]["id"])
                    #append tweet url
                    tweet_data_row.append("https://twitter.com/" + author_handle + "/status/" + tweets["data"][i]["id"])
                    #append timestamp
                    tweet_data_row.append(tweets["data"][i]["created_at"])
                    #append date
                    tweet_data_row.append(re.findall('.*?[^T]+', tweets["data"][i]["created_at"])[0])
                    #append time
                    tweet_data_row.append(re.findall('.*?[^T]+', tweets["data"][i]["created_at"])[1])
                    #append language
                    tweet_data_row.append(tweets["data"][i]["lang"])
                    #append text
                    tweet_data_row.append(tweets["data"][i]["text"])

                    #append tweet type
                    if "referenced_tweets" in tweets["data"][i]:
                        if tweets["data"][i]["referenced_tweets"][0]["type"] == "retweeted":
                            tweet_data_row.append("retweet")
                        elif tweets["data"][i]["referenced_tweets"][0]["type"] == "replied_to":
                            tweet_data_row.append("reply")
                        else:
                            tweet_data_row.append("quote")
                    else:
                        tweet_data_row.append("original")

                    #append referenced handles (does not include true mentions)
                    if "referenced_tweets" in tweets["data"][i]:
                        #replies
                        if tweets["data"][i]["referenced_tweets"][0]["type"] == "replied_to":
                            if re.search('(?<=^@).*?[^\s]+', tweets["data"][i]["text"]):
                                if re.findall('(?<=^@).*?[^\s]+', tweets["data"][i]["text"])[0] != author_handle:
                                    replies_referenced_list = re.findall('(?<=^@).*?[^\s]+', tweets["data"][i]["text"])
                                    tweet_data_row.append(replies_referenced_list[0])
                                    replies_edges_row = [author_handle, replies_referenced_list[0]]
                                    sna_edges_list.append(replies_edges_row)
                                    sna_nodes_list.append([replies_edges_row[1], replies_edges_row[1]])
                                else:
                                    tweet_data_row.append("--")
                            else:
                                tweet_data_row.append("--")

                        #retweets
                        elif tweets["data"][i]["referenced_tweets"][0]["type"] == "retweeted":
                            if re.search('(?<=^RT @).*?[^:]+', tweets["data"][i]["text"]):
                                if re.findall('(?<=^RT @).*?[^:]+', tweets["data"][i]["text"])[0] != author_handle:
                                    retweeted_referenced_list = re.findall('(?<=^RT @).*?[^:]+', tweets["data"][i]["text"])
                                    tweet_data_row.append(retweeted_referenced_list[0])
                                    retweeted_edges_row = [author_handle, retweeted_referenced_list[0]]
                                    sna_edges_list.append(retweeted_edges_row)
                                    sna_nodes_list.append([retweeted_edges_row[1], retweeted_edges_row[1]])
                                else:
                                    tweet_data_row.append("--")
                            else:
                                tweet_data_row.append("--")

                        #quotes
                        elif tweets["data"][i]["referenced_tweets"][0]["type"] == "quoted":
                            if "entities" in tweets["data"][i]:
                                    if "urls" in tweets["data"][i]["entities"]:
                                        quoted_references_list = []
                                        for s in tweets["data"][i]["entities"]["urls"]:
                                            if re.search('(?<=twitter.com/).*?(?=/status)', s["expanded_url"]):
                                                if re.findall('(?<=twitter.com/).*?(?=/status)', s["expanded_url"])[0] == author_handle:
                                                    continue
                                                else:
                                                    quoted_user = re.findall('(?<=twitter.com/).*?(?=/status)', s["expanded_url"])
                                                    if len(quoted_user) != 0:
                                                        quoted_references_list.append(quoted_user[0])
                                                        quoted_edges_row = [author_handle, quoted_user[0]]
                                                        sna_edges_list.append(quoted_edges_row)
                                                        sna_nodes_list.append([quoted_edges_row[1], quoted_edges_row[1]])
                                                    else:
                                                        tweet_data_row.append("--")
                                            else:
                                                continue
                                        join_quoted_references_string = ", ".join(quoted_references_list)
                                        tweet_data_row.append(join_quoted_references_string)
                                    else:
                                        tweet_data_row.append("--")
                            else:
                                tweet_data_row.append("--")
                        else:
                            tweet_data_row.append("--")
                    #original tweets
                    else:
                        tweet_data_row.append("--")

                    #append true mentions
                    if "referenced_tweets" in tweets["data"][i]:
                        #reply
                        if tweets["data"][i]["referenced_tweets"][0]["type"] == "replied_to":
                            reply_true_mention_candidates = re.findall('(?!\s).*?[^\s]+', tweets["data"][i]["text"])
                            reply_true_mentions_list = []
                            for reply_true_mention_candidate in reply_true_mention_candidates:
                                if not re.search('^@', reply_true_mention_candidates[reply_true_mention_candidates.index(reply_true_mention_candidate)-1]):
                                    if re.search('^@', reply_true_mention_candidate):
                                        if reply_true_mention_candidates.index(reply_true_mention_candidate) != 0:
                                            reply_true_mentions_list.append((re.sub("@", "", reply_true_mention_candidate)))
                                        else:
                                            continue
                                    else:
                                        continue
                                else:
                                    continue
                            if len(reply_true_mentions_list) == 0:
                                tweet_data_row.append("--")
                            else:
                                reply_true_mentions_string = ", ".join(reply_true_mentions_list)
                                tweet_data_row.append(reply_true_mentions_string)
                                for reply_mention_item in reply_true_mentions_list:
                                    reply_true_mentions_edges_row = [author_handle, reply_mention_item]
                                    sna_edges_list.append(reply_true_mentions_edges_row)
                                    sna_nodes_list.append([reply_true_mentions_edges_row[1], reply_true_mentions_edges_row[1]])

                        #quote
                        elif tweets["data"][i]["referenced_tweets"][0]["type"] == "quoted":
                            if re.search('@', tweets["data"][i]["text"]):
                                find_quote_mentions_list = re.findall('(?<=@).*?[^\s]+', tweets["data"][i]["text"])
                                join_quote_mentions_string = ", ".join(find_quote_mentions_list)
                                tweet_data_row.append(join_quote_mentions_string)
                                for quote_mention_item in find_quote_mentions_list:
                                    quoted_true_mentions_edges_row = [author_handle, quote_mention_item]
                                    sna_edges_list.append(quoted_true_mentions_edges_row)
                                    sna_nodes_list.append([quoted_true_mentions_edges_row[1], quoted_true_mentions_edges_row[1]])
                            else:
                                tweet_data_row.append("--")

                        #retweet
                        else:
                            tweet_data_row.append("--")

                    #original & '@' not found
                    else:
                        if re.search('@', tweets["data"][i]["text"]):
                            find_original_mentions_list = re.findall('(?<=@).*?[^\s]+', tweets["data"][i]["text"])
                            join_original_mentions_string = ", ".join(find_original_mentions_list)
                            tweet_data_row.append(join_original_mentions_string)
                            for original_mention_item in find_original_mentions_list:
                                original_mentions_edges_row = [author_handle, original_mention_item]
                                sna_edges_list.append(original_mentions_edges_row)
                                sna_nodes_list.append([original_mentions_edges_row[1], original_mentions_edges_row[1]])
                        else:
                            tweet_data_row.append("--")

                    #append hashtags
                    if "entities" in tweets["data"][i]:
                        if "hashtags" in tweets["data"][i]["entities"]:
                            hashtag_list = []
                            for hashtag_dictionary in tweets["data"][i]["entities"]["hashtags"]:
                                hashtag_list.append('#' + hashtag_dictionary["tag"])
                                hashtag_edges_list.append([author_handle, '#' + hashtag_dictionary["tag"]])
                                hashtag_nodes_list.append(['#' + hashtag_dictionary["tag"], '#' + hashtag_dictionary["tag"]])
                            join_hashtag_string = ", ".join(hashtag_list)
                            tweet_data_row.append(join_hashtag_string)
                        else:
                            tweet_data_row.append("--")
                    else:
                        tweet_data_row.append("--")

                    #append image_links
                    if "entities" in tweets["data"][i]:
                        if "urls" in tweets["data"][i]["entities"]:
                            if "images" in tweets["data"][i]["entities"]["urls"][0]:
                                tweet_data_row.append(tweets["data"][i]["entities"]["urls"][0]["images"][0]["url"])
                            else:
                                tweet_data_row.append("--")
                        else:
                            tweet_data_row.append("--")
                    else:
                        tweet_data_row.append("--")

                    #append external url data
                    if "entities" in tweets["data"][i]:
                        if "urls" in tweets["data"][i]["entities"]:
                            for url_dictionary in tweets["data"][i]["entities"]["urls"]:
                                url_list = []
                                host_list = []
                                title_list = []
                                description_list = []
                                if re.search('twitter.com', url_dictionary["expanded_url"]):
                                    continue
                                else:
                                    #append url
                                    if "unwound_url" in url_dictionary:
                                        if re.search('www\.', url_dictionary["unwound_url"]):
                                            url_list.append(re.sub('www\.', "", url_dictionary["unwound_url"]))
                                        else:
                                            url_list.append(url_dictionary["unwound_url"])
                                    else:
                                        if "expanded_url" in url_dictionary:
                                            if re.search('www\.', url_dictionary["expanded_url"]):
                                                url_list.append(re.sub('www\.', "", url_dictionary["expanded_url"]))
                                            else:
                                                url_list.append(url_dictionary["expanded_url"])
                                    #append url_host
                                    if len(url_list) == 0:
                                        host_list.append("--")
                                    else:
                                        for url in url_list:
                                            url_2 = re.sub('((?<=\..{3})|(?<=\..{2}))/.*', '', url)
                                            url_3 = re.sub('https://|http://', '', url_2)
                                            host_list.append(url_3)
                                    #append article title
                                    if "title" in url_dictionary:
                                        title_list.append(url_dictionary["title"])
                                    else:
                                        title_list.append("--")
                                    #append article description
                                    if "description" in url_dictionary:
                                        description_list.append(url_dictionary["description"])
                                    else:
                                        description_list.append("--")
                            #clean, join and append url_list
                            if len(url_list) > 1:
                                if "--" in url_list:
                                    url_index = url_list.index("--")
                                    clean_url_list = re.sub("--", "", url_list[url_index])
                                    join_clean_url_list = "".join(clean_url_list)
                                    tweet_data_row.append(join_clean_url_list)
                                else:
                                    join_url_list = ", ".join(url_list)
                                    tweet_data_row.append(join_url_list)
                            if len(url_list) == 0:
                                tweet_data_row.append("--")
                            else:
                                join_url_list = "".join(url_list)
                                tweet_data_row.append(join_url_list)
                            #clean, join and append host_list
                            if len(host_list) > 1:
                                join_host_list = ", ".join(host_list)
                                tweet_data_row.append(join_host_list)
                            if len(host_list) == 0:
                                tweet_data_row.append("--")
                            else:
                                join_host_list = "".join(host_list)
                                tweet_data_row.append(join_host_list)
                            #clean, join and append title_list
                            if len(title_list) > 1:
                                if "--" in title_list:
                                    title_index = title_list.index("--")
                                    clean_title_list = re.sub("--", "", title_list[title_index])
                                    join_clean_title_list = "".join(clean_title_list)
                                    tweet_data_row.append(join_clean_title_list)
                                else:
                                    join_title_list = ", ".join(title_list)
                                    tweet_data_row.append(join_title_list)
                            if len(title_list) == 0:
                                tweet_data_row.append("--")
                            else:
                                join_title_list = "".join(title_list)
                                tweet_data_row.append(join_title_list)
                            #clean, join and append description_list
                            if len(description_list) > 1:
                                if "--" in description_list:
                                    description_index = description_list.index("--")
                                    clean_description_list = re.sub("--", "", description_list[description_index])
                                    join_clean_description_list = "".join(clean_description_list)
                                    tweet_data_row.append(join_clean_description_list)
                                else:
                                    join_description_list = ", ".join(description_list)
                                    tweet_data_row.append(join_description_list)
                            if len(description_list) == 0:
                                tweet_data_row.append("--")
                            else:
                                join_description_list = "".join(description_list)
                                tweet_data_row.append(join_description_list)
                        else:
                            tweet_data_row.append("--")
                            tweet_data_row.append("--")
                            tweet_data_row.append("--")
                            tweet_data_row.append("--")
                    else:
                        tweet_data_row.append("--")
                        tweet_data_row.append("--")
                        tweet_data_row.append("--")
                        tweet_data_row.append("--")

                    #append retweet_count for all tweet types
                    tweet_data_row.append(tweets["data"][i]["public_metrics"]["retweet_count"])
                    #append other engagement metrics for non-original tweets; append "--" if retweet
                    if "referenced_tweets" in tweets["data"][i]:
                        if tweets["data"][i]["referenced_tweets"][0]["type"] == "retweeted":
                            tweet_data_row.append("--")
                        else:
                            tweet_data_row.append(tweets["data"][i]["public_metrics"]["reply_count"])

                        if tweets["data"][i]["referenced_tweets"][0]["type"] == "retweeted":
                            tweet_data_row.append("--")
                        else:
                            tweet_data_row.append(tweets["data"][i]["public_metrics"]["like_count"])

                        if tweets["data"][i]["referenced_tweets"][0]["type"] == "retweeted":
                            tweet_data_row.append("--")
                        else:
                            tweet_data_row.append(tweets["data"][i]["public_metrics"]["quote_count"])
                    #append engagement metrics for original tweets
                    else:
                        tweet_data_row.append(tweets["data"][i]["public_metrics"]["reply_count"])
                        tweet_data_row.append(tweets["data"][i]["public_metrics"]["like_count"])
                        tweet_data_row.append(tweets["data"][i]["public_metrics"]["quote_count"])

                    #write present iteration of tweet_data_row to .csv file
                    csv_writer.writerow(tweet_data_row)
            #iterate to next page of results
            if "meta" in tweets.keys():
                if "next_token" in tweets["meta"].keys():
                    global next_page_url
                    global next_json_response
                    global page_iteration
                    next_page_url = query_url + '&pagination_token=' + tweets['meta']['next_token']
                    next_json_response = connect_to_endpoint(next_page_url)
                    tweets = json.loads(next_json_response.text)
                    pprint(tweets)
                    print("page iteration " + str(page_iteration) + " complete")
                    page_iteration = page_iteration + 1
                else:
                    print("next_token not found")
                    break
            else:
                print('Done!')
                has_another_page = False

    for currentArgument, currentValue in arguments:
        if currentArgument in ('--sna'):
            sna_directory_name = "nodes_edges_" + query + "_" + now
            os.mkdir(sna_directory_name)
            os.chdir(sna_directory_name)
            with open(query + " sna_edges_list" + now + ".csv", "w") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(["source",
                                     "target"
                                     ])
                for edges_row in sna_edges_list:
                    csv_writer.writerow(edges_row)

            with open(query + " sna_nodes_list" + now + ".csv", "w") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(["id",
                                     "label"
                                     ])
                remove_duplicates = []
                [remove_duplicates.append(x) for x in sna_nodes_list if x not in remove_duplicates]
                for nodes_row in remove_duplicates:
                    csv_writer.writerow(nodes_row)
            os.chdir('../')

        if currentArgument in ('--json'):
            with open(query + now + ".json", "w") as json_file:
                #json_file.write(json_response.text)
                json_loads = json.loads(json_response.text)
                json.dump(json_loads, json_file, indent=2, sort_keys=True)

        if currentArgument in ('--tags'):
            hashtag_directory_name = "hashtag_list_" + query + "_" + now
            os.mkdir(hashtag_directory_name)
            os.chdir(hashtag_directory_name)
            with open(query + " hashtag_edges_list" + now + ".csv", "w") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(["source",
                                     "target"
                                     ])
                for tag_edges_row in hashtag_edges_list:
                    csv_writer.writerow(tag_edges_row)

            with open(query + " hashtag_nodes_list" + now + ".csv", "w") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(["id",
                                     "label"
                                     ])
                remove_duplicates = []
                [remove_duplicates.append(x) for x in hashtag_nodes_list if x not in remove_duplicates]
                for tag_nodes_row in remove_duplicates:
                    csv_writer.writerow(tag_nodes_row)
            os.chdir('../')

if __name__ == "__main__":
    main()
