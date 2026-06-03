# My Redis Notes

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
