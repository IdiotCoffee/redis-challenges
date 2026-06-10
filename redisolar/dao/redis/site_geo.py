from typing import Dict
from typing import List
from typing import Set

from redisolar.dao.base import SiteGeoDaoBase
from redisolar.dao.base import SiteNotFound
from redisolar.dao.redis.base import RedisDaoBase
from redisolar.models import GeoQuery
from redisolar.models import Site
from redisolar.schema import FlatSiteSchema

CAPACITY_THRESHOLD = 0.2


class SiteGeoDaoRedis(SiteGeoDaoBase, RedisDaoBase):
    """SiteGeoDaoRedis persists and queries Sites in Redis."""
    def insert(self, site: Site, **kwargs):
        """Insert a Site into Redis."""
        hash_key = self.key_schema.site_hash_key(site.id)
        client = kwargs.get('pipeline', self.redis)
        client.hset(hash_key, mapping=FlatSiteSchema().dump(site))  # type: ignore

        if not site.coordinate:
            raise ValueError("Site coordinates are required for Geo insert")

        client.geoadd(  # type: ignore
            self.key_schema.site_geo_key(), site.coordinate.lng, site.coordinate.lat,
            site.id)

    def insert_many(self, *sites: Site, **kwargs) -> None:
        """Insert multiple Sites into Redis."""
        for site in sites:
            self.insert(site, **kwargs)

    def find_by_id(self, site_id: int, **kwargs) -> Site:
        """Find a Site by ID in Redis."""
        hash_key = self.key_schema.site_hash_key(site_id)
        site_hash = self.redis.hgetall(hash_key)

        if not site_hash:
            raise SiteNotFound()

        return FlatSiteSchema().load(site_hash)

    def _find_by_geo(self, query: GeoQuery, **kwargs) -> Set[Site]:
        site_ids = self.redis.georadius(  # type: ignore
            self.key_schema.site_geo_key(), query.coordinate.lng, query.coordinate.lat,
            query.radius, query.radius_unit.value)
        sites = [
            self.redis.hgetall(self.key_schema.site_hash_key(site_id))
            for site_id in site_ids
        ]
        return {FlatSiteSchema().load(site) for site in sites}

    def _find_by_geo_with_capacity(self, query: GeoQuery, **kwargs) -> Set[Site]:
        # START Challenge #5
        # Your task: Get the sites matching the GEO query.
        # END Challenge #5

        p = self.redis.pipeline(transaction=False)

        # START Challenge #5
        #
        # Your task: Populate a dictionary called "scores" whose keys are site
        # IDs and whose values are the site's capacity.
        #
        # Make sure to run any Redis commands against a Pipeline object
        # for better performance.


        # Implementation:
        # step 1: get all the sites within given radius
        lat = query.coordinate.lat
        long = query.coordinate.lng
        key = self.key_schema.site_geo_key()
        rad = query.radius
        unit = query.radius_unit.value
        
        site_ids = self.redis.georadius(key, long, lat, rad, unit=unit) # type: ignore

        # now, get all the capacity keys:
        capacity_ranking_key = self.key_schema.capacity_ranking_key()
        
        scores: Dict[str, float] = {}
        # find the capacities (using zscore to get the score of the capacity with site_id as the corresponding value):
        for site_id in site_ids:
            p.zscore(capacity_ranking_key, site_id)
        # p.execute can be run later - basically, you need to understand when / where to optimally execute your pipeline.
        
        scores = {site_id: capacity for site_id, capacity in zip(site_ids, capacities)}
        # END Challenge #5

        for site_id in site_ids:
            if scores[site_id] and scores[site_id] > CAPACITY_THRESHOLD:
                p.hgetall(self.key_schema.site_hash_key(site_id))
        site_hashes = p.execute()

        return {FlatSiteSchema().load(site) for site in site_hashes}

    def find_by_geo(self, query: GeoQuery, **kwargs) -> Set[Site]:
        """Find Sites using a geographic query."""
        if query.only_excess_capacity:
            return self._find_by_geo_with_capacity(query)
        return self._find_by_geo(query)

    def find_all(self, **kwargs) -> Set[Site]:
        """Find all Sites."""
        site_ids = self.redis.zrange(self.key_schema.site_geo_key(), 0, -1)
        sites = set()
        # Optional Challenge:
        p = self.redis.pipeline(transaction=False)
        for site_id in site_ids:
            key = self.key_schema.site_hash_key(site_id)
            site_hash = client.hgetall(key)
        # to be done in 2 parts, not one - and remove the execute command, caller runs it already.
        site_hashes =p.execute()
        for site_hash in site_hashes:
            sites.add(FlatSiteSchema().load(site_hash))

        return sites
