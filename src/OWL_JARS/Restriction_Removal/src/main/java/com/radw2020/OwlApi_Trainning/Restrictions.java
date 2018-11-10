package com.radw2020.OwlApi_Trainning;

import java.util.Collections;
import java.util.HashSet;
import java.util.Set;
import java.io.File;
import org.semanticweb.owlapi.model.*;
import org.junit.Test;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.IRI;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLClassExpression;
import org.semanticweb.owlapi.model.OWLDocumentFormat;
import org.semanticweb.owlapi.model.OWLObjectProperty;
import org.semanticweb.owlapi.model.OWLObjectPropertyExpression;
import org.semanticweb.owlapi.model.OWLObjectSomeValuesFrom;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyCreationException;
import org.semanticweb.owlapi.model.OWLOntologyManager;
import org.semanticweb.owlapi.model.OWLOntologyStorageException;
import org.semanticweb.owlapi.model.OWLSubClassOfAxiom;
import org.semanticweb.owlapi.util.OWLClassExpressionVisitorAdapter;

    public class Restrictions 
    {
        
        public static void main(String[] args) 
        {
                
            try 
            {
                Restrictions del_restrictions = new Restrictions();
                del_restrictions.shouldLookAtRestrictions(args[0], args[1], args[2], args[3]);
            } 
            catch (OWLOntologyCreationException ex) 
            {
                System.out.println(ex);
            }
        }
    
        /** This example shows how to examine the restrictions on a class.
         * 
         * @throws OWLOntologyCreationException */
        @Test
        public void shouldLookAtRestrictions(String Dom_IRI, String Property_IRI, String Range_IRI, String f) throws OWLOntologyCreationException 
        {
            OWLOntologyManager man = OWLManager.createOWLOntologyManager();
            File file = new File(f);
            OWLOntology ont = man.loadOntologyFromOntologyDocument(file);

            /* We want to examine the restrictions on margherita pizza. To do this,
            we need to find a reference to the margherita pizza class. In this
            case, we know the URI for margherita pizza ( A class may have a URI 
            that bears no resemblance to the ontology URI which contains axioms 
            about the class). */

            IRI Domain_IRI = IRI.create(Dom_IRI);
            OWLClass Domain_class = man.getOWLDataFactory()
                    .getOWLClass(Domain_IRI);

            /* Now we want to collect the properties which are used in existential
            restrictions on the class. To do this, we will create a utility class
            - RestrictionVisitor, which acts as a filter for existential
            restrictions. */ 

            RestrictionVisitor restrictionVisitor = new RestrictionVisitor(
                    Collections.singleton(ont));

            /* In this case, restrictions are used as (anonymous) superclasses, so
            to get the restrictions on margherita pizza we need to obtain the
            subclass axioms for margherita pizza. */

            Set<OWLSubClassOfAxiom> axioms_to_remove = new HashSet<OWLSubClassOfAxiom>();
            for (OWLSubClassOfAxiom ax : ont.getSubClassAxiomsForSubClass(Domain_class)) 
            {
                boolean isfound = ax.toString().contains(Range_IRI);
                if(isfound)
                {
                    OWLClassExpression superCls = ax.getSuperClass();
                    axioms_to_remove.add(ax);
                    System.out.println(superCls);

                    /* Ask our superclass to accept a visit from the RestrictionVisitor
                    - if it is an existential restiction then our restriction visitor
                    will answer it - if not our visitor will ignore it */

                    superCls.accept(restrictionVisitor);
                }
            }

            System.out.println(ont.getAxiomCount());
            for(OWLSubClassOfAxiom ax: axioms_to_remove)
            {
                    for(OWLObjectProperty prop: ax.getObjectPropertiesInSignature())
                    {
                            if( prop.toString().equals("<"+Property_IRI+">") )
                            {
                                    RemoveAxiom removeAx = new RemoveAxiom(ont, ax);
                                    man.applyChange(removeAx);
                                    break;
                            }
                    }
            }
            OWLDocumentFormat format = man.getOntologyFormat(ont);
            try
            {
                    man.saveOntology( ont, format, IRI.create(file.toURI()) );
            }
            catch(OWLOntologyStorageException e)
            {
                    System.out.println(e);
            }
        
            System.out.println(ont.getAxiomCount());
        }
        
        /** Visits existential restrictions and collects the properties which are
         * restricted */
        private static class RestrictionVisitor extends OWLClassExpressionVisitorAdapter {
            private final Set<OWLClass> processedClasses;
            private final Set<OWLObjectPropertyExpression> restrictedProperties;
            private final Set<OWLOntology> onts;

            public RestrictionVisitor(Set<OWLOntology> onts) {
                restrictedProperties = new HashSet<>();
                processedClasses = new HashSet<>();
                this.onts = onts;
            }

            public Set<OWLObjectPropertyExpression> getRestrictedProperties() {
                return restrictedProperties;
            }

            @Override
            /* If we are processing inherited restrictions then we
            recursively visit named supers. Note that we need to keep
            track of the classes that we have processed so that we don't
            get caught out by cycles in the taxonomy */
            public void visit(OWLClass desc) {
                if (!processedClasses.contains(desc)) {
                    processedClasses.add(desc);
                    onts.forEach((ont) -> {
                        ont.getSubClassAxiomsForSubClass(desc).forEach((ax) -> {
                            ax.getSuperClass().accept(this);
                        });
                    });
                }
            }

            @Override
            /* This method gets called when a class expression is an existential
                (someValuesFrom) restriction and it asks us to visit it */
            public void visit(OWLObjectSomeValuesFrom desc) {
                restrictedProperties.add(desc.getProperty());
            }
        }
    }
