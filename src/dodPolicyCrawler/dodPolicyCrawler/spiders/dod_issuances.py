import scrapy
import re
import bs4


class ExampleSpider(scrapy.Spider):
    name = "dod_issuances"
    start_urls = ['https://www.esd.whs.mil/DD/DoD-Issuances/DTM/']
    allowed_domains = ['www.esd.whs.mil']

    def parse(self, response):
        links = response.css('li.col-sm-6')[0].css('a')
        yield from response.follow_all(links[4:-1], self.parse_documents)
        pass

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
                    #pdf_url = abs_url(
                    #    base_url, cell.a['href']).replace(' ', '%20')
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
                elif opr_idx and idx == opr_idx:
                    office_primary_resp = self.fix_oprs(data)

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
            print(fields)
            yield doc_item
