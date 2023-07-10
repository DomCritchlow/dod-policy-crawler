import scrapy
import re
import bs4
from urllib.parse import urljoin, urlparse
from os.path import splitext
import datetime
from dodPolicyCrawler.items import DodpolicycrawlerItem
from dodPolicyCrawler.utils import dict_to_sha256_hex_digest

class DoDIssuances(scrapy.Spider):
    name = "dod_issuances"
    start_urls = ['https://www.esd.whs.mil/DD/DoD-Issuances/DTM/']
    allowed_domains = ['www.esd.whs.mil']

    @staticmethod
    def get_href_file_extension(url: str) -> str:
        """
            returns file extension if exists in passed url path, else UNKNOWN
            UNKNOWN is used so that if the website fixes their link it will trigger an update from the doc type changing
        """
        path = urlparse(url).path
        ext: str = splitext(path)[1].replace('.', '').lower()

        if not ext:
            return "Unkown"

        return ext.strip()

    @staticmethod
    def get_pub_date(publication_date):
        '''
        This function convverts publication_date from DD Month YYYY format to YYYY-MM-DDTHH:MM:SS format.
        T is a delimiter between date and time.
        '''
        try:
            date = parse_timestamp(publication_date, None)
            if date:
                publication_date = datetime.strftime(date, '%Y-%m-%dT%H:%M:%S')
        except:
            publication_date = ""
        return publication_date

    @staticmethod
    def get_display_doc_type(doc_type):
        display_dict = {
            "dod": 'Issuance',
            "dodm": 'Manual',
            "dodi": 'Instruction',
            "dodd": 'Directive',
            "ai": 'Instruction',
            "dtm": 'Memorandum'
            }
        return display_dict.get(doc_type, "Document")
    
    def parse(self, response):
        links = response.css('li.col-sm-6')[0].css('a')
        yield from response.follow_all(links[4:-1], self.parse_documents)

    def parse_documents(self, response):

        page_url = response.url

        # parse html response
        base_url = 'https://www.esd.whs.mil'
        soup = bs4.BeautifulSoup(response.body, features="html.parser")
        table = soup.find('table', attrs={'class': 'dnnGrid'})
        rows = table.find_all('tr')

        page_url_clean = page_url.lower()

        # set issuance type
        if page_url_clean.endswith('dodd/'):
            doc_type = 'DoDD'
        elif page_url_clean.endswith('dodi/'):
            doc_type = 'DoDI'
        elif page_url_clean.endswith('dodm/'):
            doc_type = 'DoDM'
        elif page_url_clean.endswith('inst/'):
            doc_type = 'AI'
        elif page_url_clean.endswith('dtm/'):
            doc_type = 'DTM'
        else:
            doc_type = 'DoDI CPM'

        # iterate through each row of the table
        cac_required = ['CAC', 'PKI certificate required',
                        'placeholder', 'FOUO']

        opr_idx = None
        for oidx, header in enumerate(rows[0].find_all('th')):
            if header.text.strip() == "OPR":
                opr_idx = oidx

        for row in rows[1:]:

            # reset variables to ensure there is no carryover between rows
            doc_num = ''
            doc_name = ''
            doc_title = ''
            chapter_date = ''
            publication_date = ''
            cac_login_required = False
            pdf_url = ''
            exp_date = ''
            issuance_num = ''
            pdf_di = None
            office_primary_resp = ''

            # skip the extra rows, not included in the table
            try:
                row['class']  # all invalid rows do not have a class attribute
            except:
                continue

            # iterate through each cell of row
            for idx, cell in enumerate(row.find_all('td')):

                # remove unwanted characters
                data = re.sub(r'\s*[\n\t\r\s+]\s*', ' ', cell.text).strip()

                # set document variables based on current column
                if idx == 0:
                    #pdf_url = abs_url(base_url, cell.a['href']).replace(' ', '%20')
                    pdf_url = urljoin(base_url, cell.a['href']).replace(' ', '%20')
                    pdf_di = {
                        "doc_type": 'pdf',
                        "download_url": pdf_url,
                        "compression_type": None
                    }

                    # remove parenthesis from document name
                    data = re.sub(r'\(.*\)', '', data).strip()

                    # set doc_name and doc_num based on issuance
                    if page_url_clean.endswith('dtm/'):
                        doc_name = data
                        doc_num = re.search(r'\d{2}.\d{3}', data)[0]
                    elif page_url_clean.endswith('140025/'):
                        issuance_num = data.split()
                        doc_name = 'DoDI 1400.25 Volume ' + issuance_num[0] if issuance_num[0] != 'DoDI' \
                            else ' '.join(issuance_num).strip()

                        doc_num = issuance_num[0] if issuance_num[0] != 'DoDI' \
                            else issuance_num[-1]
                    else:
                        doc_name = data
                        doc_num = data.split(' ')[1] if data.find(
                            ' ') != -1 else data.split('-')[-1]

                elif idx == 1:
                    publication_date = data
                elif idx == 2:
                    doc_title = data
                elif idx == 3:
                    doc_name = doc_name + ' ' + data if data != '' else doc_name
                elif idx == 4:
                    chapter_date = data
                elif idx == 5:
                    exp_date = data

                # set boolean if CAC is required to view document
                cac_login_required = True if any(x in pdf_url for x in cac_required) \
                    or any(x in doc_title for x in cac_required) else False

            fields = {
                "doc_name": doc_name,
                "doc_num": doc_num,
                "doc_title": doc_title,
                "doc_type": doc_type,
                "cac_login_required": cac_login_required,
                "page_url": page_url,
                "pdf_url": pdf_url,
                "pdf_di": pdf_di,
                "publication_date": publication_date,
                "chapter_date": chapter_date,
                "office_primary_resp": office_primary_resp
            }
            doc_item = self.populate_doc_item(fields)
            #print(fields)
            yield doc_item#"doc_item_placeholder"#doc_item


    def populate_doc_item(self, fields):
        '''
        This functions provides both hardcoded and computed values for the variables
        in the imported DocItem object and returns the populated metadata object
        '''
        display_org = "Dept. of Defense" # Level 1: GC app 'Source' filter for docs from this crawler
        data_source = "WHS DoD Directives Division" # Level 2: GC app 'Source' metadata field for docs from this crawler
        source_title = "Unlisted Source" # Level 3 filter
        is_revoked = False
        cac_login_required = fields.get("cac_login_required")
        source_page_url = fields.get("page_url")
        office_primary_resp = fields.get("office_primary_resp")

        doc_name = fields.get("doc_name").strip()
        doc_title = re.sub('\\"', '', fields.get("doc_title"))
        doc_num = fields.get("doc_num").strip()
        doc_type = fields.get("doc_type").strip()
        publication_date = fields.get("publication_date").strip()
        publication_date = self.get_pub_date(publication_date)
        display_source = data_source + " - " + source_title
        display_title = doc_type + " " + doc_num + ": " + doc_title
        display_doc_type = self.get_display_doc_type(doc_type.lower())
        download_url = fields.get("pdf_url")
        file_type = self.get_href_file_extension(download_url)
        downloadable_items = [fields.get("pdf_di")]
        version_hash_fields = {
                "download_url": download_url,
                "pub_date": publication_date,
                "change_date": fields.get("chapter_date").strip(),
                "doc_num": doc_num,
                "doc_name": doc_name,
                "display_title": display_title
            }
        source_fqdn = urlparse(source_page_url).netloc
        version_hash = dict_to_sha256_hex_digest(version_hash_fields)

        return DodpolicycrawlerItem(
                doc_name = doc_name,
                doc_title = doc_title,
                doc_num = doc_num,
                doc_type = doc_type,
                display_doc_type = display_doc_type,
                publication_date = publication_date,
                cac_login_required = cac_login_required,
                crawler_used = self.name,
                downloadable_items = downloadable_items,
                source_page_url = source_page_url,
                source_fqdn = source_fqdn,
                download_url = download_url, 
                version_hash_raw_data = version_hash_fields,
                version_hash = version_hash,
                display_org = display_org,
                data_source = data_source,
                source_title = source_title,
                display_source = display_source,
                display_title = display_title,
                file_ext = file_type,
                is_revoked = is_revoked,
                office_primary_resp = office_primary_resp,
            )
