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
