import urllib.parse
from items import PersonItem
from bs4 import BeautifulSoup
import datetime


class MorganLewisParser:

    @classmethod
    def parse(cls, response, preview_record, record_details):
        publications = cls.parse_publications(response)

        item = PersonItem()
        item['profile_url'] = preview_record.get('profile_url')
        item['photo_url'] = preview_record.get('photo_url')
        item['full_name'] = preview_record.get('name')
        item['position'] = preview_record.get('position')
        item['phone_numbers'] = preview_record.get('phone_number')
        item['email'] = preview_record.get('email')
        item['services'] = record_details.get('services')
        item['sectors'] = record_details.get('sectors')
        item['publications'] = publications
        item['person_brief'] = record_details.get('brief')
        item['crawled_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return item

    @classmethod
    def parse_preview_records(cls, response, domain=None):
        soup = BeautifulSoup(response.text, 'lxml')
        div_cards = soup.findAll('div', {'class': 'c-content-team__card'})
        card_keys = ['photo_url', 'profile_url', 'email', 'name', 'position', 'phone_number']
        for div in div_cards:
            data = []
            img = div.findChild('img')
            if not img:
                continue
            data.append(cls.build_full_link(img.get('src'), domain))

            a_tags = div.findChildren('a')
            if not a_tags:
                continue
            data.append(cls.build_full_link(a_tags[0].get('href'), domain))
            data.append(cls.parse_mail(a_tags[2].get('href')))

            div_name = div.findChild('div', {'class': 'c-content-team__name'})
            if div_name is None:
                continue
            data.append(div_name.get_text())

            div_position = div.findChild('div', {'class': 'c-content-team__title'})
            if div_position is None:
                continue
            data.append(div_position.get_text())

            span_phone_tags = div.findChildren('span', {'class': 'c-content-team__number'})
            if not span_phone_tags:
                continue
            phones = [span.get_text() for span in span_phone_tags]
            data.append(phones)
            yield dict(zip(card_keys, data))

    @classmethod
    def parse_record_details(cls, response):
        soup = BeautifulSoup(response.text, 'lxml')
        sectors_div = soup.find('div', {'class': 'person-depart-info'})
        services_section = soup.find('section', {'class': 'person-depart-info'})
        sectors = cls.parse_li_tags_data(sectors_div)
        services = cls.parse_li_tags_data(services_section)
        item_id = cls.parse_item_id(response)
        brief_div = soup.find('div', {'class': 'purple-para arrow-class'})
        brief = None
        if brief_div is not None:
            brief = cls.clean_string(brief_div.get_text())
        data = {'sectors': sectors, 'services': services, 'item_id': item_id, 'brief': brief}
        return data

    @classmethod
    def parse_item_id(cls, response):
        vcard_link = response.selector.xpath('//p[@class="v-card"]/a/@href').get()
        if not vcard_link:
            return
        vcard_link_clean = urllib.parse.unquote_plus(vcard_link)
        item_id = vcard_link_clean.split('{')[-1].strip('}')
        return item_id

    @classmethod
    def parse_li_tags_data(cls, tag):
        if not tag:
            return
        li_tags = tag.findChildren('li')
        data = []
        for li in li_tags:
            data.append(cls.clean_string(li.get_text()))
        if not data:
            return
        return data

    @classmethod
    def parse_publications(cls, response):
        soup = BeautifulSoup(response.text, 'lxml')
        publications_p_tags = soup.findAll('p')
        publications_list = []
        for publication_p_tag in publications_p_tags:
            publications_list.append(publication_p_tag.get_text())
        if not publications_list:
            return publications_list
        return publications_list[:-1]

    @staticmethod
    def build_full_link(link, domain):
        return f'https://{domain}{link}'

    @staticmethod
    def parse_mail(mail_link):
        return mail_link.split('mailto:')[-1].strip()

    @staticmethod
    def clean_string(string):
        if not string:
            return ''
        return ' '.join(string.split())
