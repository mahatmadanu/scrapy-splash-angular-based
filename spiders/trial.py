import scrapy
from scrapy_splash import SplashRequest
from scrapy.selector import HtmlXPathSelector
import json
from csv import DictWriter

# import Request

class ArticleSpider(scrapy.Spider):
    name = "woolworths"
    result = []
    url = "https://www.woolworths.com.au/shop/browse/bakery"
    start_urls = []

    min_page = 1
    #should be changed manually
    max_page = 21

    page_number = "?pageNumber="

    while min_page<=max_page:
        page = str(min_page)
        start_urls.append(url+page_number+page)
        int(min_page)
        min_page += 1
    

    def start_requests(self):
        
        for url in self.start_urls:

            yield SplashRequest(url, self.parse,
                endpoint='render.html',
                args={'wait': 20},
            )


    def parse(self, response):
        res = []
        hxs = response
        main = hxs.xpath("//main[@class='shop-centerPanel']")
        cp = main.xpath('//div/wow-tile-list-with-content')
        ng = main.xpath('//ng-transclude/wow-browse-tile-list/wow-tile-list')
        tile_list = ng.xpath('//div[@class="tileList-tiles"]')
        div_tile_container = response.xpath('//div[@class="tile-container tile-product"]')

        for idx,content in enumerate(div_tile_container):
            prodContent = content.xpath('.//div[@class="shelfProductTile-content"]')

            prodInformation = prodContent.xpath('.//div[@class="shelfProductTile-information"]')
            produrl = prodInformation.xpath('.//h3[@class="shelfProductTile-description"]/a/@href').extract()
            prodimage = content.xpath('.//div[@class="shelfProductTile-content"]/a/img/@src').extract()

            data ={
                'produrl': produrl[0] if len(produrl)>0 else "" ,
                'prodimage': prodimage[0] if len(prodimage)>0 else ""
            }
            #find product details
            absolute_url = 'https://www.woolworths.com.au'+produrl[0]
            yield SplashRequest(absolute_url, callback=self.parse_attr,args={'wait': 20}, meta={"item":data})
            self.result.append(data)

    def parse_attr(self, response):
        add_details = {}
        add_details_labels = ['Ingredients', 'NutritionInformation', 'Allergen']
        item = response.meta['item']
        anutrition = []

        #find prodname prod price in box container
        product_details_container = response.css('.productDetail-tile')

        prod_name = product_details_container.xpath('//h1[@class="productDetail-tileName heading3"]/text()').extract_first()
        prod_name = prod_name.replace("\n","")
        prod_name = prod_name.strip()

        prod_price_detail_symbol = product_details_container.css('span.price-symbol::text').extract_first()
        prod_price_detail_value = product_details_container.css('span.price-dollars::text').extract_first()
        prod_price_detail_cent = product_details_container.css('span.price-cents::text').extract_first()
        prod_price_detail_unit = product_details_container.xpath('//div[@class="productDetail-priceCup"]/text()').extract_first()

        #find product detail and additional details
        proddetails_content = response.xpath('(//div[@class="productDetail-widthAdjust"])[2]')

        prod_detail = proddetails_content.xpath('//div[@class="viewMore"]//p/text()').extract()
        prod_details_value = {
            'detail' : "|".join(prod_detail) 
        }        
    
        #create title content
        adddetails_titles = proddetails_content.xpath("//h3/text()").extract()
        for idx, title in enumerate(adddetails_titles):
            value = title.replace(" ","")
            index = idx + 4
            print(value)
            if value == "Ingredients":
                detail = proddetails_content.xpath('div['+str(index)+']//p/text()').extract()
                add_details[value] = "|".join(detail)

            elif value == "NutritionInformation":
                detail = proddetails_content.xpath('div['+str(index)+']//p/text()').extract()
                # print(detail)
                add_details[value] = "|".join(detail)
            
            elif value == "Allergen":
                detail = proddetails_content.xpath('div['+str(index)+']//p/text()').extract()
                # print(detail)
                add_details[value] = "|".join(detail)

        prod_details_value["additional"] = add_details
        

        item['proddetail'] = prod_details_value['detail']
        for label in add_details_labels:
            if prod_details_value["additional"].get(label) == None:
                item[label] = "-"
            else:
                item[label]= prod_details_value["additional"][label]
        # #extract nutririon table
        # # if detail2_h == 'Nutrition Information':
        # #     atable_nut = []
        # #     serv_per_pkg = proddetailscontent.xpath('div[5]/div[1]/text()').extract_first()
        # #     serv_size = proddetailscontent.xpath('div[5]/div[2]/text()').extract_first()
        # #     table_nut = proddetailscontent.xpath('div[5]//table[@class="productDetail-nutritionTable"]//tbody/tr')
        # #     for row in table_nut:
        # #         dict_table_nut = {
        # #             'Nutrition' : row.xpath('td[1]//text()').extract_first(),
        # #             'Avg_Qty_Per_Serving': row.xpath('td[2]//text()').extract_first(),
        # #             'handle_Avg_Qty_Per_100g' : row.xpath('td[3]//text()').extract_first(),
        # #         }
        # #         atable_nut.append(dict_table_nut) test

        item['prodname'] = prod_name
        item['prodprice']=prod_price_detail_symbol+prod_price_detail_value+"."+prod_price_detail_cent
        item['unit']=prod_price_detail_unit
        
        return item