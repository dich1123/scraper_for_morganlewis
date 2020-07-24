import pprint


class PrintingPipeline:

    def process_item(self, item, spider):
        pprint.pprint(item)
