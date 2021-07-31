import requests
import wget
import bs4
import os
import urllib.parse
from PIL import Image
from io import BytesIO
import fnmatch
import re
import sys
import requests
from Bio import Entrez, SeqIO
import json

####################
## Z bazy danych czasopisma BMC Systems Biology ze strony (https://bmcsystbiol.biomedcentral.com/articles) pobierz i
## zapisz do folderu BaseArticles informacje, które obejmują jakiś miesiąc danego roku, np. grudzień 2018:
# a) jeden plik tekstowy (nazwa pliku = nazwa miesiąca) zawierający kolejno informacje (tytuł artykułu, autorzy,
# zawartość abstraktu) z artykułów obejmujących zadany okres
# b) jeżeli w tytule artykułu wystąpiło słowo ’network lub networks’ zapisz również plik pdf artykułu do folderu

## Odczyt kodu HTML ##
url = 'https://bmcsystbiol.biomedcentral.com/articles?tab=keyword&searchType=journalSearch&sort=PubDate&volume=12&page=1'
codeHTML = requests.get(url, verify=True).text # odczyt zawartości strony (HTML)
# #print(codeHTML)
soup = bs4.BeautifulSoup(codeHTML, 'html.parser') # tworzenie obiektu BeautifulSoup z zachowaniem struktury kodu strony
# #print(soup) # wyświetlenie kodu z zachowaniem struktury

f1 = open("grudzien.txt","w+", encoding="utf-8") #zapis z miesiąca grudnia

articles_list = list(soup.findAll('article', attrs = {'class' : 'c-listing'}))
#print("ARTYKULY Z GRUDNIA: " + str(len(articles_list)))
print("(INFO) Zapisuje dane do pliku grudzien.txt i pobieram pdf'y")

for article in articles_list:
    if (article.find("span", {"itemprop": "datePublished"}).text.endswith("December 2018"))==True:
        url= "https://bmcsystbiol.biomedcentral.com" + str(article.find("a").get('href'))
        f1.write("LINK DO ARTYKULU ---> " + url + "\n")
        ### przejście na strone danego artykułu
        codeHTML = requests.get(url, verify=True).text
        soup = bs4.BeautifulSoup(codeHTML, 'html.parser')
        title=soup.find("meta", {"name": "dc.title"}).get("content")
        x = re.findall("NETWORK", title.upper()) # szukanie artykułów z "network" w stringu
        if x: # jeśli "network" w str to pobiera pdf
            article_page = soup.find('div', attrs={'class': 'c-pdf-download u-clear-both'})
            pdf = "https:" + str(article_page.find("a").get('href'))
            f1.write("LINK DO PDFA ---> " + pdf + "\n")
            response = requests.get(pdf)
            open("C:\\Users\\Przemek\\PycharmProjects\\scraping\\zapis\\" + pdf.rsplit('/', 1)[-1], 'wb').write(response.content)
        f1.write("TYTUL ---> " + title + "\n")
        f1.write("AUTORZY ---> ")
        for authors in soup.findAll("meta", {"name": "dc.creator"}):
            f1.write(authors.get("content") + "    ")
        f1.write("\nZAWARTOSC ABSTRACT ---> " + soup.find("meta", {"property": "og:description"}).get("content") + "\n\n\n")

f1.close()

####################
## Napisz program, który umożliwi użytkownikowi pobranie określonych danych z medycznej bazy danych emedicine
## (https://emedicine.medscape.com/)


url = 'https://emedicine.medscape.com/'
codeHTML = requests.get(url, verify=True).text
soup = bs4.BeautifulSoup(codeHTML, 'html.parser')

categories = soup.find('div', attrs = {'class' : 'browse-medicine'})
categories_list=list(categories.findAll("a"))

### wyświetlanie 30-tu kategorii dostępnych w BROWSE BY SPECIALITY: MEDICINE
i=0
for category in categories_list:
    categories_list[i]=category.text
    i+=1

categories_list={index+1:value for index,value in enumerate(categories_list)}
print(categories_list)

### wybieranie do której kategorii mamy wejść
choice=categories_list.get(int(input('Którą kategorie wybierasz?: ')))
print(choice)

### przechodzenie na strone konkretnej kategorii
for category in soup.findAll("a"):
    if(category.text==choice):
        if(category.get("href").startswith("http")):
            subpage=category.get("href")
        else:
            subpage="https://emedicine.medscape.com" + str(category.get("href"))

url = subpage
codeHTML = requests.get(url, verify=True).text
soup = bs4.BeautifulSoup(codeHTML, 'html.parser')

### wyświetlanie podkategorii z wcześniej wybranej kategorii
topics=soup.findAll("div", {"class": "topic-head"})
i=0
for topic in topics:
    topics[i]=topic.text
    i+=1

topics_list={index+1:value for index,value in enumerate(topics)}
print(topics_list)

### wybieranie podkategorii z którą będziemy pracować
choice=topics_list.get(int(input('Którą podkategorie wybierasz?: ')))
print(choice)

values = topics_list.values()
values_list = list(values)
index = values_list.index(choice)


subcategories=soup.findAll('div', attrs = {"class": "topic-section"})[index]

### wchodzenie po kolei do każdej podkategorii
subcategories=subcategories.findAll("a")
for subcategory in subcategories:
    link=subcategory.get("href")
    #print(link)
    codeHTML2 = requests.get(link, verify=True).text
    soup2 = bs4.BeautifulSoup(codeHTML2, 'html.parser')

    title=soup2.find('span', attrs={"class": "nav-title-name"})
    title=title.text
    #print(title)

    ## pobieranie zdjęć z podkategorii (jeśli są)
    try:
        image = soup2.find('div', attrs={"class": "imgWrapper"}).get("data-rel")
        image = "http:" + image
        #print(image)
        img = Image.open(requests.get(image, stream=True).raw)
        img.save("C:\\Users\\Przemek\\PycharmProjects\\scraping\\zdjecia\\" + image.split("/")[-1], 'PNG')
    except:
       print("!!! An exception occurred")

    ## zapisywanie tekstu z background (jeśli jest)
    try:
        menu_list = soup2.find('div', attrs={"id": "menuWrapper"})
        menu_list = menu_list.findAll("a")
        for menu in menu_list:
            if (menu.text == "Background"):
                f1 = open('C:\\Users\\pwolc\\PycharmProjects\\lab8_bioinf\\venv\\BazaTekst\\' + title + '.txt', "w+",
                          encoding="utf-8")
                content_nr = menu.get("href")[1:]
                # print(content_nr)
                content_nr = "content_" + content_nr
                backgroundDiv = soup2.find('div', {"id": content_nr})
                if (backgroundDiv is not None):
                    for paragraph in backgroundDiv.find_all('p'):
                        for sup in paragraph.findAll('sup'):
                            sup.extract()
                        f1.write(paragraph.text + "\n")
    except:
        print("An exception occurred")

print("(INFO) Pobrałem artykuły z wybranej podkategorii do folderu BazaTekst")
print("(INFO) Pobrałem zdjęcia z artykułów do folderu BazaImage")


####################
## Połącz się z Entrez - systemem wyszukiwania informacji w NCBI.
## Sprawdż ile publikacji w bazie PubMed znajduje się na temat 'covid-19' (parametr term)

Entrez.email = "pwolczacki@gmail.com"
info = Entrez.esearch(db = "pubmed",term = "covid-19")  # m.in przedstawia listę identyfikatorów UID pasujących do zapytania tekstowego
print("\n########## ZAD 1, LAB 9\nPublikacje w bazie PubMed na temat 'covid-19': " + Entrez.read(info)['Count'])

####################
### Połącz się z Entrez - systemem wyszukiwania informacji w NCBI.
### W bazie danych nucleotide wyszukaj informacje dla kwerendy: 'covid'
## a) wypisz wszystkie UID  dla w/w kwerendy (key: IdList)

Entrez.email = "pwolczacki@gmail.com"
info = Entrez.esearch(db = "nucleotide",term = "covid")
record = Entrez.read(info)
print("\n########## ZAD 2, LAB 9\na) Wszystkie UID dla kwerendy 'covid' w bazie Nucleotide: " + str(record['IdList']))

UID=record['IdList'][2]
#print(type(UID))
info = Entrez.efetch(db = "nucleotide", id = str(UID), rettype="gb", retmode="xml")
#record = Entrez.read(info)
#print(record)
records = Entrez.parse(info)

## b) dla 3-go znalezionego UID odczytaj (użyj funkcji efetch z parametrem retmode="xml")
## dodatkowe informacje z bazy "nucleotide":
# (i) nazwę tego biomarkera/cząstki
# (ii) z jakiego organizmu były pobrane próbki do badań

for record in records:
    print("b) Nazwa biomarkera/cząstki: " + record['GBSeq_locus'])
    print("Próbki do badań pobrane z: " + record['GBSeq_organism'])

####################
## Połącz się z Entrez - systemem wyszukiwania informacji w NCBI.
## Wyszukaj informacje o sekwencji  id = 'NC_045512'
## odpowiedz na pytania:
# (a) Jak długa jest sekwencja nukleotydowa?
# (b) Od jakiego organizmu pochodzi?
# (c) Kiedy opublikowano pierwsze wyniki?
# (d) Czy ta sekwencja była kiedykolwiek poprawiana/aktualizowana? (kolejne wersje?)
# (e) Kto jest pierwszym autorem badań sekwencji?
# (f) Gdzie (w jakich czasopismach) opublikowano wyniki badań tej sekwencji po zgłoszeniu w bazie (wszystkie publikacje)
# (g) Jaką część sekwencji opisano jako gen (ang. gene)? Jak długi jest ten fragment? I jaką nazwę genu
# przypisano temu fragmentowi?
# (h) Przełącz się na widok w formacie FASTA. Spróbuj rozszyfrować, co wpisano jako opis sekwencji.

Entrez.email = "pwolczacki@gmail.com"
info = Entrez.efetch(db="nucleotide", id="NC_045512", rettype="gb", retmode="xml")
#record = Entrez.read(info)
#print(record)
#print(json.dumps(record, sort_keys=True, indent=4))

records = Entrez.parse(info)

for record in records:
    print("\n########## ZAD 3, LAB 9\na) Długość sekwencji nukleotydowej: " + record['GBSeq_length'])
    print("b) Nazwa organizmu: " + record['GBSeq_organism'])
    print("c) Pierwsze wyniki opublikowano: " + record['GBSeq_create-date'])
    print("d) Czy aktualizowano?: " +
          ("Tak" if record['GBSeq_update-date'] != record['GBSeq_create-date'] else "Nie"))
    print("e) Pierwsi autorzy: " +
          str((record['GBSeq_references'][0]['GBReference_authors'])))
    print("f) Publikacje badań: ")
    for ref in record['GBSeq_references']:
        print("    " + ref['GBReference_journal'])
    print("g) ")
    for ref in record['GBSeq_feature-table']:
        if (ref['GBFeature_key'] == 'gene'):
            print("Długość fragmentu części sekwencji opisanej jako gen (ang. gene): ", ref['GBFeature_location'])
            print("Nazwa genu: ", ref['GBFeature_quals'][0]['GBQualifier_value'])

print("\n h) Opis w formacie .FASTA:\n" + SeqIO.read(Entrez.efetch(
    db="nucleotide", id="NC_045512", rettype="fasta"), "fasta").description)


