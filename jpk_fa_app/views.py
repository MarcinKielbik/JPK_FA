import xml.etree.ElementTree as ET
from django.shortcuts import render
from django.http import HttpResponse
from .models import JPK_FA, Invoice, Item
from decimal import Decimal

def process_file(request):
    if request.method == 'POST' and request.FILES.getlist('file'):
        input_files = request.FILES.getlist('file')
        for input_file in input_files:
            naglowek_content, podmiot_content, faktury_content, faktura_wiersz_content, liczba_wierszy, wartosc_wierszy = process_jpk_fa(input_file)
            output_file = 'processed_data.xml'
            generate_xml(naglowek_content, podmiot_content, faktury_content, faktura_wiersz_content, liczba_wierszy, wartosc_wierszy, output_file)
        response = HttpResponse('Plik JPK_FA został przetworzony.')
        return response
    return render(request, 'process_file.html')



def process_jpk_fa(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    namespaces = {
        "xsd": "http://www.w3.org/2001/XMLSchema",
        "etd": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2018/08/24/eD/DefinicjeTypy/",
        "tns": "http://jpk.mf.gov.pl/wzor/2022/02/17/02171/"
    }

    naglowek_data = root.find("./tns:Naglowek", namespaces)
    naglowek_content = ET.tostring(naglowek_data, encoding="unicode") if naglowek_data is not None else ""

    podmiot_data = root.find("./tns:Podmiot1", namespaces)
    podmiot_content = ET.tostring(podmiot_data, encoding="unicode") if podmiot_data is not None else ""

    faktury_data = root.findall("./tns:Faktura", namespaces)
    faktury_content = [ET.tostring(faktura, encoding="unicode") for faktura in faktury_data]

    faktura_wiersz_data = root.findall("./tns:FakturaWiersz", namespaces)
    faktura_wiersz_content = [ET.tostring(faktura_wiersz, encoding="unicode") for faktura_wiersz in faktura_wiersz_data]

    liczba_wierszy = len(faktury_data)
    wartosc_wierszy = str(sum([Decimal(faktura.find("./tns:P_11", namespaces).text) for faktura in faktura_wiersz_data if faktura.find("./tns:P_11", namespaces) is not None]))

    merged_faktura_wiersz_content = merge_faktura_wiersz_tags(faktura_wiersz_content, namespaces)

    return naglowek_content, podmiot_content, faktury_content, merged_faktura_wiersz_content, liczba_wierszy, wartosc_wierszy


def merge_faktura_wiersz_tags(faktura_wiersz_content, namespaces):
    merged_faktura_wiersz_content = []
    summary_dict = {}

    for faktura_wiersz_content_item in faktura_wiersz_content:
        faktura_wiersz_element = ET.fromstring(faktura_wiersz_content_item)

        common_name = faktura_wiersz_element.find("./tns:P_2B", namespaces).text

        vat_rate = faktura_wiersz_element.find("./tns:P_12", namespaces).text

        if vat_rate == "23":
            p_7_text = "Sprzedaż usług"
        elif vat_rate == "19":
            p_7_text = "Sprzedaż export"
        elif vat_rate == "np":
            p_7_text = "Sprzedaż oss"
        else:
            p_7_text = ""  # Domyślna wartość, jeśli vat_rate nie spełnia warunków

        p8a = faktura_wiersz_element.find("./tns:P_8A", namespaces).text
        p8b = faktura_wiersz_element.find("./tns:P_8B", namespaces).text

        if common_name not in summary_dict:
            summary_dict[common_name] = {
                'p_9a_sum': Decimal(0),
                'p_9b_sum': Decimal(0),
                'p_11_sum': Decimal(0),
                'vat_rate': vat_rate,
                'p_7_text': p_7_text,
                'p8a': p8a,
                'p8b': p8b
            }

        if faktura_wiersz_element.find("./tns:P_9A", namespaces) is not None:
            p_9a_text = faktura_wiersz_element.find("./tns:P_9A", namespaces).text
            summary_dict[common_name]['p_9a_sum'] += Decimal(p_9a_text)

        if faktura_wiersz_element.find("./tns:P_9B", namespaces) is not None:
            p_9b_text = faktura_wiersz_element.find("./tns:P_9B", namespaces).text
            summary_dict[common_name]['p_9b_sum'] += Decimal(p_9b_text)

        if faktura_wiersz_element.find("./tns:P_11", namespaces) is not None:
            p_11_text = faktura_wiersz_element.find("./tns:P_11", namespaces).text
            summary_dict[common_name]['p_11_sum'] += Decimal(p_11_text)

    for common_name, summary_values in summary_dict.items():
        new_faktura_wiersz_element = ET.Element("{" + namespaces['tns'] + "}FakturaWiersz")
        p_2b_element = ET.SubElement(new_faktura_wiersz_element, "{" + namespaces['tns'] + "}P_2B")
        p_2b_element.text = common_name

        p_7_element = ET.SubElement(new_faktura_wiersz_element, "{" + namespaces['tns'] + "}P_7")
        p_7_element.text = summary_values['p_7_text']

        p_8a_element = ET.SubElement(new_faktura_wiersz_element, "{" + namespaces['tns'] + "}P_8A")
        p_8a_element.text = summary_values['p8a']

        p_8b_element = ET.SubElement(new_faktura_wiersz_element, "{" + namespaces['tns'] + "}P_8B")
        p_8b_element.text = summary_values['p8b']

        p_9a_element = ET.SubElement(new_faktura_wiersz_element, "{" + namespaces['tns'] + "}P_9A")
        p_9a_element.text = str(summary_values['p_9a_sum'])

        p_9b_element = ET.SubElement(new_faktura_wiersz_element, "{" + namespaces['tns'] + "}P_9B")
        p_9b_element.text = str(summary_values['p_9b_sum'])

        p_11_element = ET.SubElement(new_faktura_wiersz_element, "{" + namespaces['tns'] + "}P_11")
        p_11_element.text = str(summary_values['p_11_sum'])

        p_12_element = ET.SubElement(new_faktura_wiersz_element, "{" + namespaces['tns'] + "}P_12")
        p_12_element.text = summary_values['vat_rate']

        merged_faktura_wiersz_content.append(ET.tostring(new_faktura_wiersz_element, encoding="unicode"))

    return merged_faktura_wiersz_content




def generate_xml(naglowek_content, podmiot_content, faktury_content, faktura_wiersz_content, liczba_wierszy,
                 wartosc_wierszy, output_file):
    namespaces = {
        "xsd": "http://www.w3.org/2001/XMLSchema",
        "etd": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2018/08/24/eD/DefinicjeTypy/",
        "tns": "http://jpk.mf.gov.pl/wzor/2022/02/17/02171/"
    }

    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)

    # Utwórz główny element JPK z prefiksem i przestrzenią nazw
    jpk_element = ET.Element("{" + namespaces['tns'] + "}JPK")

    # Parsuj zawartość nagłówka i podmiotu
    naglowek_element = ET.fromstring(naglowek_content)
    podmiot_element = ET.fromstring(podmiot_content)

    # Dodaj nagłówek i podmiot do elementu JPK
    jpk_element.append(naglowek_element)
    jpk_element.append(podmiot_element)

    # Iteruj przez faktury i dodaj je do odpowiednich elementów
    for faktura_content in faktury_content:
        faktura_element = ET.fromstring(faktura_content)
        jpk_element.append(faktura_element)

    # Dodaj przetworzone wiersze faktur
    for faktura_wiersz_content_item in faktura_wiersz_content:
        faktura_wiersz_element = ET.fromstring(faktura_wiersz_content_item)
        jpk_element.append(faktura_wiersz_element)

    # Dodaj kontroler wierszy faktur
    faktura_wiersz_ctrl_element = ET.SubElement(jpk_element, "{" + namespaces['tns'] + "}FakturaWierszCtrl")
    liczba_wierszy_element = ET.SubElement(faktura_wiersz_ctrl_element,
                                           "{" + namespaces['tns'] + "}LiczbaWierszyFaktur")
    wartosc_wierszy_element = ET.SubElement(faktura_wiersz_ctrl_element,
                                            "{" + namespaces['tns'] + "}WartoscWierszyFaktur")
    liczba_wierszy_element.text = str(liczba_wierszy)
    wartosc_wierszy_element.text = str(wartosc_wierszy)

    # Zapisz strukturę XML do pliku
    xml_tree = ET.ElementTree(jpk_element)
    xml_tree.write(output_file, encoding='utf-8', xml_declaration=True)

    return output_file


