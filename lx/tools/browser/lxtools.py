# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Acquisition import aq_inner
from plone.memoize.instance import memoize
from lxml import etree
from mediawiki import wiki2html
import re
import logging
from zope.site.hooks import getSite
from zope.component import queryUtility
from plone.i18n.normalizer.interfaces import IIDNormalizer
from xml.etree.ElementTree import iterparse


class LxToolsView(BrowserView):
    """Lx Tools"""

    __call__ = ViewPageTemplateFile('templates/lxtools.pt')

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.errors = {}

    def settings(self):
        if 'form.action.reindexIndexObject' in self.request.form:
            tipo_conteudo = self.request.get('tipo.conteudo', None)
            index_conteudo = self.request.get('index.conteudo', None)
            if self.validateReindexIndex(tipo_conteudo, index_conteudo):
                return self.reindexIndexObject(tipo_conteudo, index_conteudo)
        if 'form.action.parseXML' in self.request.form:
            file_xml = self.request.get('fileXML', None)
            folder_conteudo = self.request.get('folderMediaWiki', None)
            if self.validateParseXML(file_xml, folder_conteudo):
                return self.parseXML(file_xml, folder_conteudo)


    def validateReindexIndex(self, tipo_conteudo, index_conteudo):
        """Validação do Reindex.
        """
        context = aq_inner(self.context)
        utils = getToolByName(context, 'plone_utils')
        if tipo_conteudo == None:
            self.errors['tipo_conteudo'] = "O campo é obrigatório."
        if index_conteudo == None:
            self.errors['index_conteudo'] = "O campo é obrigatório."
        # Check for errors
        if self.errors:
            utils.addPortalMessage("Corrija os erros.", type='error')
            return False
        else:
            return True

    def reindexIndexObject(self, tipo_conteudo, index_conteudo):
        """Reindex.
        """
        context = aq_inner(self.context)
        utils = getToolByName(context, 'plone_utils')
        ctool = getToolByName(self, 'portal_catalog')
        objects = ctool(portal_type=tipo_conteudo, sort_on='id', sort_order='ascending')
        log = logging.getLogger('REINDEX:')
        for object in objects:
            obj = object.getObject()
            try:
                obj.reindexObject(idxs=index_conteudo)
                log.info(obj.absolute_url_path() + ' CATALOGADO')
            except:
                log.info(obj.absolute_url_path() + ' ERRO')
        msg = 'Procedimento executado.'
        utils.addPortalMessage(msg, type='info')

    @memoize
    def getTypes(self):
        """
        """
        putils = getToolByName(self, 'plone_utils')
        allTypes = putils.getUserFriendlyTypes()
        allTypes = allTypes
        return sorted(allTypes, key=str.lower)

    @memoize
    def getIndexes(self):
        """Retorna todos os indices do catalog.
        """
        ctool = getToolByName(self, 'portal_catalog')
        indexs = ctool.getIndexObjects()
        indexs = [i.getId() for i in indexs]
        return sorted(indexs, key=str.lower)

    @memoize
    def validateParseXML(self, file_xml, folder_conteudo):
        """Validação do Parse XML.
        """
        context = aq_inner(self.context)
        utils = getToolByName(context, 'plone_utils')
        if file_xml.filename == '':
            self.errors['file_xml'] = "O campo é obrigatório."
        if (folder_conteudo == '') or (folder_conteudo.strip() == ''):
            self.errors['folder_conteudo'] = "O campo é obrigatório."
        # Check for errors
        if self.errors:
            utils.addPortalMessage("Corrija os erros.", type='error')
            return False
        else:
            return True
        
    @memoize
    def parseXML(self, file_xml, folder_conteudo):
        """Parse XML.
        https://github.com/zikzakmedia/python-mediawiki
        """
        context = aq_inner(self.context)
        utils = getToolByName(context, 'plone_utils')

        NS = '{http://www.mediawiki.org/xml/export-0.3/}'
        
        conteudo = []

        with open(file_xml.name) as f:
            for event, elem in iterparse(f):
                if elem.tag == '{0}page'.format(NS):
                    title = elem.find("{0}title".format(NS))
                    contr = elem.find(".//{0}username".format(NS))
                    text = elem.find(".//{0}text".format(NS))
                    if (title is not None) and (contr is not None) and (text is not None):
                        text = unicode(text.text).encode('utf-8')
                        text = wiki2html(text, True)
                        conteudo.append(dict(title=title.text, contr=contr.text, text=text))
                    elem.clear()

        self.createDocument(conteudo, folder_conteudo)

        msg = 'Procedimento executado.'
        utils.addPortalMessage(msg, type='info')
        
    def createDocument(self, conteudo, folder_conteudo):
        """
        """
        log = logging.getLogger('createDocument:')
        
        site = getSite()
        id_folder = queryUtility(IIDNormalizer).normalize(folder_conteudo)
        
        if not hasattr(site, id_folder):
            site.invokeFactory('Folder', id=id_folder, title=folder_conteudo)
        
        folderMediaWiki = getattr(site, id_folder)
        for i in conteudo:
            id = queryUtility(IIDNormalizer).normalize(i['title'])
            if not hasattr(folderMediaWiki, id):
                folderMediaWiki.invokeFactory('Document', id=id, title=i['title'])
                page = getattr(folderMediaWiki, id)
                page.setText(i['text'], mimetype='text/html')
                log.info(id)
