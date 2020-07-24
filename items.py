from scrapy import Item, Field


class PersonItem(Item):
    profile_url = Field()
    photo_url = Field()
    full_name = Field()
    position = Field()
    phone_numbers = Field()
    email = Field()
    services = Field()
    sectors = Field()
    publications = Field()
    person_brief = Field()
    crawled_time = Field()
