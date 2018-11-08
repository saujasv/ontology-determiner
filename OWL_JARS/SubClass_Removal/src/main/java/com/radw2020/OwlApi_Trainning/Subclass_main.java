package com.radw2020.OwlApi_Trainning;

import org.semanticweb.owlapi.model.OWLOntologyCreationException;
import java.io.File;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.IRI;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLDocumentFormat;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyManager;
import org.semanticweb.owlapi.model.OWLOntologyStorageException;
import org.semanticweb.owlapi.model.OWLSubClassOfAxiom;

public class Subclass_main {
    
    public static void main(String[] args) throws OWLOntologyCreationException
    {
        
        OWLOntologyManager man = OWLManager.createOWLOntologyManager();
        System.out.println(args[0]);
        System.out.println(args[1]);
        System.out.println(args[2]);
        File file = new File(args[2]);
        OWLOntology ont = man.loadOntologyFromOntologyDocument(file);
        OWLClass superClass = man.getOWLDataFactory()
                .getOWLClass(IRI.create(args[1])); 
        OWLClass subClass = man.getOWLDataFactory().getOWLClass(IRI.create(args[0]));
        OWLSubClassOfAxiom Subclass_axiom = man.getOWLDataFactory().getOWLSubClassOfAxiom(subClass, superClass);
        System.out.println(Subclass_axiom);
        System.out.println(ont.getAxiomCount());
        RemoveAxiom removeAx = new RemoveAxiom(ont, Subclass_axiom);
        man.applyChange(removeAx);
        OWLDocumentFormat format = man.getOntologyFormat(ont);
        try
        {
                man.saveOntology( ont, format, IRI.create(file.toURI()) );
                System.out.println(ont.getAxiomCount());
        }
        catch(OWLOntologyStorageException e)
        {
                System.out.println(e);
        }
        
    }
    
}
