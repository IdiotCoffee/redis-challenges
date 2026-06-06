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
