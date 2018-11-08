package com.radw2020.OwlApi_Trainning;

import org.semanticweb.owlapi.model.OWLOntologyCreationException;
import static java.util.Collections.singleton;
import java.io.File;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.IRI;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLDocumentFormat;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyManager;
import org.semanticweb.owlapi.model.OWLOntologyStorageException;
import org.semanticweb.owlapi.util.OWLEntityRemover;

public class Class_main {
    
    public static void main(String[] args) throws OWLOntologyCreationException
    {
        
        OWLOntologyManager man = OWLManager.createOWLOntologyManager();
        File file = new File(args[1]);
        OWLOntology ont = man.loadOntologyFromOntologyDocument(file);
        OWLClass Domain_class = man.getOWLDataFactory()
                .getOWLClass(IRI.create(args[0])); 
        System.out.println(Domain_class);

        OWLEntityRemover remover = new OWLEntityRemover(singleton(ont));
        for (OWLClass ind : ont.getClassesInSignature()) 
        {
                if( ind.toString().equals(Domain_class.toString()) )
                {
                        ind.accept(remover);
                        break;
                }
        }
        System.out.println(ont.getClassesInSignature().size());
        man.applyChanges(remover.getChanges());
        OWLDocumentFormat format = man.getOntologyFormat(ont);
        try
        {
                man.saveOntology( ont, format, IRI.create(file.toURI()) );
        }
        catch(OWLOntologyStorageException e)
        {
                System.out.println(e);
        }
        System.out.println(ont.getClassesInSignature().size());
        
    }
    
}
