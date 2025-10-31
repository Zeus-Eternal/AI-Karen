/**
 * Translation Resources
 * 
 * Default translation resources for the application
 */

import type { TranslationResources } from './index';

export const defaultResources: TranslationResources = {
  en: {
    common: {
      // Navigation
      navigation: {
        dashboard: 'Dashboard',
        chat: 'Chat',
        memory: 'Memory',
        plugins: 'Plugins',
        models: 'Models',
        workflows: 'Workflows',
        settings: 'Settings',
        admin: 'Admin',
      },
      
      // Actions
      actions: {
        save: 'Save',
        cancel: 'Cancel',
        delete: 'Delete',
        edit: 'Edit',
        create: 'Create',
        update: 'Update',
        search: 'Search',
        filter: 'Filter',
        sort: 'Sort',
        export: 'Export',
        import: 'Import',
        refresh: 'Refresh',
        retry: 'Retry',
        close: 'Close',
        open: 'Open',
        submit: 'Submit',
        reset: 'Reset',
        clear: 'Clear',
        copy: 'Copy',
        paste: 'Paste',
        cut: 'Cut',
        undo: 'Undo',
        redo: 'Redo',
      },
      
      // Status
      status: {
        loading: 'Loading...',
        saving: 'Saving...',
        saved: 'Saved',
        error: 'Error',
        success: 'Success',
        warning: 'Warning',
        info: 'Information',
        online: 'Online',
        offline: 'Offline',
        connected: 'Connected',
        disconnected: 'Disconnected',
        active: 'Active',
        inactive: 'Inactive',
        enabled: 'Enabled',
        disabled: 'Disabled',
      },
      
      // Time
      time: {
        now: 'Now',
        today: 'Today',
        yesterday: 'Yesterday',
        tomorrow: 'Tomorrow',
        thisWeek: 'This week',
        lastWeek: 'Last week',
        nextWeek: 'Next week',
        thisMonth: 'This month',
        lastMonth: 'Last month',
        nextMonth: 'Next month',
        thisYear: 'This year',
        lastYear: 'Last year',
        nextYear: 'Next year',
      },
      
      // Pluralization examples
      items: {
        zero: 'No items',
        one: '{{count}} item',
        other: '{{count}} items',
      },
      
      users: {
        zero: 'No users',
        one: '{{count}} user',
        other: '{{count}} users',
      },
      
      // Accessibility
      accessibility: {
        skipToMain: 'Skip to main content',
        skipToNavigation: 'Skip to navigation',
        skipToSearch: 'Skip to search',
        openMenu: 'Open menu',
        closeMenu: 'Close menu',
        toggleTheme: 'Toggle theme',
        increaseFontSize: 'Increase font size',
        decreaseFontSize: 'Decrease font size',
        highContrast: 'High contrast mode',
        reducedMotion: 'Reduced motion',
        screenReaderOnly: 'Screen reader only',
      },
      
      // Forms
      forms: {
        required: 'Required',
        optional: 'Optional',
        invalid: 'Invalid',
        valid: 'Valid',
        placeholder: 'Enter {{field}}',
        validation: {
          required: 'This field is required',
          email: 'Please enter a valid email address',
          minLength: 'Must be at least {{min}} characters',
          maxLength: 'Must be no more than {{max}} characters',
          pattern: 'Please match the requested format',
        },
      },
      
      // Errors
      errors: {
        generic: 'An error occurred',
        network: 'Network error',
        timeout: 'Request timeout',
        unauthorized: 'Unauthorized',
        forbidden: 'Forbidden',
        notFound: 'Not found',
        serverError: 'Server error',
        validation: 'Validation error',
        retry: 'Please try again',
      },
    },
    
    dashboard: {
      title: 'Dashboard',
      welcome: 'Welcome to Kari AI',
      overview: 'Overview',
      metrics: 'Metrics',
      charts: 'Charts',
      widgets: 'Widgets',
    },
    
    chat: {
      title: 'Chat',
      placeholder: 'Type your message...',
      send: 'Send',
      thinking: 'Thinking...',
      typing: 'Typing...',
      newConversation: 'New conversation',
      clearHistory: 'Clear history',
    },
    
    settings: {
      title: 'Settings',
      general: 'General',
      appearance: 'Appearance',
      language: 'Language',
      accessibility: 'Accessibility',
      privacy: 'Privacy',
      security: 'Security',
      notifications: 'Notifications',
      advanced: 'Advanced',
    },
  },
  
  es: {
    common: {
      navigation: {
        dashboard: 'Panel de Control',
        chat: 'Chat',
        memory: 'Memoria',
        plugins: 'Complementos',
        models: 'Modelos',
        workflows: 'Flujos de Trabajo',
        settings: 'Configuración',
        admin: 'Administrador',
      },
      
      actions: {
        save: 'Guardar',
        cancel: 'Cancelar',
        delete: 'Eliminar',
        edit: 'Editar',
        create: 'Crear',
        update: 'Actualizar',
        search: 'Buscar',
        filter: 'Filtrar',
        sort: 'Ordenar',
        export: 'Exportar',
        import: 'Importar',
        refresh: 'Actualizar',
        retry: 'Reintentar',
        close: 'Cerrar',
        open: 'Abrir',
        submit: 'Enviar',
        reset: 'Restablecer',
        clear: 'Limpiar',
        copy: 'Copiar',
        paste: 'Pegar',
        cut: 'Cortar',
        undo: 'Deshacer',
        redo: 'Rehacer',
      },
      
      status: {
        loading: 'Cargando...',
        saving: 'Guardando...',
        saved: 'Guardado',
        error: 'Error',
        success: 'Éxito',
        warning: 'Advertencia',
        info: 'Información',
        online: 'En línea',
        offline: 'Sin conexión',
        connected: 'Conectado',
        disconnected: 'Desconectado',
        active: 'Activo',
        inactive: 'Inactivo',
        enabled: 'Habilitado',
        disabled: 'Deshabilitado',
      },
      
      items: {
        zero: 'Sin elementos',
        one: '{{count}} elemento',
        other: '{{count}} elementos',
      },
      
      users: {
        zero: 'Sin usuarios',
        one: '{{count}} usuario',
        other: '{{count}} usuarios',
      },
      
      accessibility: {
        skipToMain: 'Saltar al contenido principal',
        skipToNavigation: 'Saltar a la navegación',
        skipToSearch: 'Saltar a la búsqueda',
        openMenu: 'Abrir menú',
        closeMenu: 'Cerrar menú',
        toggleTheme: 'Cambiar tema',
        increaseFontSize: 'Aumentar tamaño de fuente',
        decreaseFontSize: 'Disminuir tamaño de fuente',
        highContrast: 'Modo de alto contraste',
        reducedMotion: 'Movimiento reducido',
        screenReaderOnly: 'Solo para lector de pantalla',
      },
    },
    
    dashboard: {
      title: 'Panel de Control',
      welcome: 'Bienvenido a Kari AI',
      overview: 'Resumen',
      metrics: 'Métricas',
      charts: 'Gráficos',
      widgets: 'Widgets',
    },
    
    chat: {
      title: 'Chat',
      placeholder: 'Escribe tu mensaje...',
      send: 'Enviar',
      thinking: 'Pensando...',
      typing: 'Escribiendo...',
      newConversation: 'Nueva conversación',
      clearHistory: 'Limpiar historial',
    },
    
    settings: {
      title: 'Configuración',
      general: 'General',
      appearance: 'Apariencia',
      language: 'Idioma',
      accessibility: 'Accesibilidad',
      privacy: 'Privacidad',
      security: 'Seguridad',
      notifications: 'Notificaciones',
      advanced: 'Avanzado',
    },
  },
  
  fr: {
    common: {
      navigation: {
        dashboard: 'Tableau de Bord',
        chat: 'Chat',
        memory: 'Mémoire',
        plugins: 'Extensions',
        models: 'Modèles',
        workflows: 'Flux de Travail',
        settings: 'Paramètres',
        admin: 'Administrateur',
      },
      
      actions: {
        save: 'Enregistrer',
        cancel: 'Annuler',
        delete: 'Supprimer',
        edit: 'Modifier',
        create: 'Créer',
        update: 'Mettre à jour',
        search: 'Rechercher',
        filter: 'Filtrer',
        sort: 'Trier',
        export: 'Exporter',
        import: 'Importer',
        refresh: 'Actualiser',
        retry: 'Réessayer',
        close: 'Fermer',
        open: 'Ouvrir',
        submit: 'Soumettre',
        reset: 'Réinitialiser',
        clear: 'Effacer',
        copy: 'Copier',
        paste: 'Coller',
        cut: 'Couper',
        undo: 'Annuler',
        redo: 'Refaire',
      },
      
      status: {
        loading: 'Chargement...',
        saving: 'Enregistrement...',
        saved: 'Enregistré',
        error: 'Erreur',
        success: 'Succès',
        warning: 'Avertissement',
        info: 'Information',
        online: 'En ligne',
        offline: 'Hors ligne',
        connected: 'Connecté',
        disconnected: 'Déconnecté',
        active: 'Actif',
        inactive: 'Inactif',
        enabled: 'Activé',
        disabled: 'Désactivé',
      },
      
      items: {
        zero: 'Aucun élément',
        one: '{{count}} élément',
        other: '{{count}} éléments',
      },
      
      users: {
        zero: 'Aucun utilisateur',
        one: '{{count}} utilisateur',
        other: '{{count}} utilisateurs',
      },
      
      accessibility: {
        skipToMain: 'Aller au contenu principal',
        skipToNavigation: 'Aller à la navigation',
        skipToSearch: 'Aller à la recherche',
        openMenu: 'Ouvrir le menu',
        closeMenu: 'Fermer le menu',
        toggleTheme: 'Basculer le thème',
        increaseFontSize: 'Augmenter la taille de police',
        decreaseFontSize: 'Diminuer la taille de police',
        highContrast: 'Mode contraste élevé',
        reducedMotion: 'Mouvement réduit',
        screenReaderOnly: 'Lecteur d\'écran uniquement',
      },
    },
    
    dashboard: {
      title: 'Tableau de Bord',
      welcome: 'Bienvenue sur Kari AI',
      overview: 'Aperçu',
      metrics: 'Métriques',
      charts: 'Graphiques',
      widgets: 'Widgets',
    },
    
    chat: {
      title: 'Chat',
      placeholder: 'Tapez votre message...',
      send: 'Envoyer',
      thinking: 'Réflexion...',
      typing: 'Frappe...',
      newConversation: 'Nouvelle conversation',
      clearHistory: 'Effacer l\'historique',
    },
    
    settings: {
      title: 'Paramètres',
      general: 'Général',
      appearance: 'Apparence',
      language: 'Langue',
      accessibility: 'Accessibilité',
      privacy: 'Confidentialité',
      security: 'Sécurité',
      notifications: 'Notifications',
      advanced: 'Avancé',
    },
  },
  
  // Add more languages as needed
  de: {
    common: {
      navigation: {
        dashboard: 'Dashboard',
        chat: 'Chat',
        memory: 'Speicher',
        plugins: 'Plugins',
        models: 'Modelle',
        workflows: 'Arbeitsabläufe',
        settings: 'Einstellungen',
        admin: 'Administrator',
      },
      
      actions: {
        save: 'Speichern',
        cancel: 'Abbrechen',
        delete: 'Löschen',
        edit: 'Bearbeiten',
        create: 'Erstellen',
        update: 'Aktualisieren',
        search: 'Suchen',
        filter: 'Filtern',
        sort: 'Sortieren',
        export: 'Exportieren',
        import: 'Importieren',
        refresh: 'Aktualisieren',
        retry: 'Wiederholen',
        close: 'Schließen',
        open: 'Öffnen',
        submit: 'Senden',
        reset: 'Zurücksetzen',
        clear: 'Löschen',
        copy: 'Kopieren',
        paste: 'Einfügen',
        cut: 'Ausschneiden',
        undo: 'Rückgängig',
        redo: 'Wiederholen',
      },
      
      status: {
        loading: 'Laden...',
        saving: 'Speichern...',
        saved: 'Gespeichert',
        error: 'Fehler',
        success: 'Erfolg',
        warning: 'Warnung',
        info: 'Information',
        online: 'Online',
        offline: 'Offline',
        connected: 'Verbunden',
        disconnected: 'Getrennt',
        active: 'Aktiv',
        inactive: 'Inaktiv',
        enabled: 'Aktiviert',
        disabled: 'Deaktiviert',
      },
      
      items: {
        zero: 'Keine Elemente',
        one: '{{count}} Element',
        other: '{{count}} Elemente',
      },
      
      users: {
        zero: 'Keine Benutzer',
        one: '{{count}} Benutzer',
        other: '{{count}} Benutzer',
      },
    },
    
    dashboard: {
      title: 'Dashboard',
      welcome: 'Willkommen bei Kari AI',
      overview: 'Übersicht',
      metrics: 'Metriken',
      charts: 'Diagramme',
      widgets: 'Widgets',
    },
    
    chat: {
      title: 'Chat',
      placeholder: 'Nachricht eingeben...',
      send: 'Senden',
      thinking: 'Denkt nach...',
      typing: 'Tippt...',
      newConversation: 'Neue Unterhaltung',
      clearHistory: 'Verlauf löschen',
    },
    
    settings: {
      title: 'Einstellungen',
      general: 'Allgemein',
      appearance: 'Erscheinungsbild',
      language: 'Sprache',
      accessibility: 'Barrierefreiheit',
      privacy: 'Datenschutz',
      security: 'Sicherheit',
      notifications: 'Benachrichtigungen',
      advanced: 'Erweitert',
    },
  },
};