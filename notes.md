# Reference Notes

## Challenge 1: Making the find_all() function work
For this challenge, first I checked the insert() method of SiteDaoRedis class. In this method, I understood how I could get the `name` of the set that held the site ids.
First, ofcourse, we need to connect to the redis client. Then, get the `site_ids_key`.
Now, we need to check the members that exist in the set containing the ids. For this, I used redis.smembers() command.
Then, iterate through the members and find the site hash for each member. Add the hash to site_hashes array.
Code becomes:

```
client = self.redis
site_ids_key = self.key_schema.site_ids_key()
sites = client.smembers(site_ids_key)
site_hashes = []
# iterate and add the hashes...
for site_id in sites:
    hash_key = self.key_schema.site_hash_key(site_id)
    site_hash = self.redis.hgetall(hash_key)
    site_hashes.append(site_hash)
return {FlatSiteSchema().load(site_hash) for site_hash in site_hashes}
```

## Challenge 2: Making the insert_metric() function work
For this challenge, first, we need to make the value that we need to insert - this can be done by calling the `__str__()` method of MeasurementMinute class. Then, to add the value, we need to use `zadd` method of the redis client. Since it is a pipeline method, we can use `pipeline.zadd()`. The method uses a key, which is already given to us, and a mapping of `{value: score}` - **NOT THE OTHER WAY AROUND**

Hence, the simple, straightforward solution becomes:

```
# START Challenge #2
# first, make the value that I need to insert.
val = MeasurementMinute(value, minute_of_day).__str__()
pipeline.zadd(metric_key, {val: minute_of_day})
# END Challenge #2
```

## Challenge 3: Using Transactions and Lua Scripting
Lua is a cool language and I should learn it sometime. It has the power to run its script within redis **atomically**. This challenge asked me to optimize an "update" function. For this, initially, there were 3 network round trips to be made, one for each update, and 3 updates each. The updates were not atomic.
What I did was - I added 3 scripts into a pipeline, and I executed the pipeline. The 3 lua scripts ensured atomicity during critical sections, and the pipeline improved performance by reducing total round trips.

```
  reporting_time = datetime.datetime.utcnow().isoformat()
  self.redis.hset(key, SiteStats.LAST_REPORTING_TIME, reporting_time)
  self.redis.hincrby(key, SiteStats.COUNT, 1)
  self.redis.expire(key, WEEK_SECONDS)
  max_wh = SiteStats.MAX_WH
  min_wh = SiteStats.MIN_WH
  max_capacity = SiteStats.MAX_CAPACITY
  script = CompareAndUpdateScript(pipeline)
  script.update_if_greater(pipeline, key, max_wh , meter_reading.wh_generated)
  script.update_if_less(pipeline, key, min_wh , meter_reading.wh_generated)
  script.update_if_greater(pipeline, key, max_capacity , meter_reading.current_capacity)
```

## Challenge 4: Site Capacity Leaderboards
Before this challenge, I was taught how to use zadd and zrange commands. zrevrange and zrange allow us to get a range of items starting from an index. In the introduction to redis course, I learnt that the `zrank()` command will get me the rank of the item in the sorted set. However, in this situation, the items are going to be added in the reverse order, with the capacity of the site that is MAXIMUM coming last. The site having LEAST capacity will be ranked first position. Hence, when I solved challenge 4, the main goal was to allow the users to check the site capacity and return it in reverse order, so that the person having HIGHEST capacity would be shown a lower value. This was done by using the `zrevrank()` command.

```
    def get_rank(self, site_id: int, **kwargs) -> float:
        # START Challenge #4
        # Remove the following line after you have added code to
        # get the real rank.
        client = kwargs.get('pipeline', self.redis)
        capacity_ranking_key = self.key_schema.capacity_ranking_key()
        rank = client.zrevrank(capacity_ranking_key, site_id)
        return rank
        # END Challenge #4
```

## Optional Challenge 1: Using Pipelines to Optimize calls:
Here, I was shown a piece of code that:
a. Got a bunch of site ids
b. For each site, used hgetall to find the actual sites in redis for the site ids.

This was using a for loop, which meant multiple round trips - 1 for getting the site_ids, and then inside the for loop, n more to get all n sites. n + 1 total round trips. This challenge asked me to use pipelining to improve the efficiency. 
I could not use a pipeline for the entire operation, as there were 2 sequential steps, in which step 2 depended on step 1 - I had to know the site_ids before I iterated through them. Hence, I used pipelining only in part 2 - instead of iterating through n times, I used a pipeline, and reduced n network calls to 1 - now, there would be a total of 2 network calls made. I initialize a pipeline AFTER i get the site_ids, and then I add the hgetall() command to the pipeline inside the for-loop, and outside the for-loop, I execute the pipeline.

```
        # Optional Challenge:
        client = kwargs.get('pipeline', self.redis)
        for site_id in site_ids:
            key = self.key_schema.site_hash_key(site_id)
            site_hash = client.hgetall(key)
            sites.add(FlatSiteSchema().load(site_hash))
        if client != self.redis:
            client.execute()
```
