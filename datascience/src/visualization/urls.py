import urllib2
from lxml import etree

lista = ['http://www.resultados.gob.ar/bltgetelegr/ICIR04001.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04002.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04003.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04004.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04005.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04006.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04007.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04008.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04009.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04010.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04011.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04012.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04013.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04014.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04015.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04016.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04017.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04018.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04019.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04020.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04021.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04022.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04023.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04024.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04025.htm',
'http://www.resultados.gob.ar/bltgetelegr/ICIR04026.htm']


lista_circuitos = list()
lista_mesas = list()
for link in lista:
	response = urllib2.urlopen(link)
	html = response.read()
	tree = etree.HTML(html)
	for tr in tree.xpath("//div/ul"):
		lista_circuitos = list()
		lista = tr.xpath("//li/a")
		for element in lista:
			lista_circuitos.append("http://www.resultados.gob.ar/bltgetelegr/" + element.get("href"))
		for element in lista_circuitos:
			response = urllib2.urlopen(element)
			html = response.read()
			tree = etree.HTML(html)
			nombre_circuito = str(element.split(".")[-2])[-4:]
			file_ = file(nombre_circuito + ".csv","w+")
			print nombre_circuito
			for tr in tree.xpath("//div/ul"):
				lista_mesas = list()
				lista = tr.xpath("//li/a")
				for element in lista:
					lista_mesas.append("http://www.resultados.gob.ar/bltgetelegr/" + element.get("href"))
				for mesa in lista_mesas:
					response = urllib2.urlopen(mesa)
					html = response.read()
					tree = etree.HTML(html)
					numero_mesa = str(mesa.split(".")[-2])[-4:]
					try:
						votos_partidos = tree.xpath("//table[@id='TVOTOS']/tbody/tr/td")
						votos_nulos = tree.xpath("//td[@class='colorborde_colpr']")[0].text
						votos_blancos = tree.xpath("//td[@class='colorborde_colpr']")[1].text
						votos_recurridos = tree.xpath("//td[@class='colorborde_colpr']")[2].text
						votos_fpv = votos_partidos[0].text
						votos_cambiemos = votos_partidos[1].text
						total = int(votos_cambiemos) + int(votos_fpv) + int(votos_recurridos) + int(votos_blancos) + int(votos_nulos)
						string = (nombre_circuito+","+numero_mesa+","+votos_fpv+","+votos_cambiemos+","+votos_blancos+","+votos_nulos+","+votos_recurridos + "," + str(total) + "\n")	
						file_.write(string)
					except:
						print "mesa:" + numero_mesa + " error "
						continue