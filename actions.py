from assembla.error import AssemblaError
import logging
FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT)

logger = logging.getLogger('ATMT')
logger.setLevel(logging.DEBUG)

def prettify(changes):
    if isinstance(changes,str) or isinstance(changes,unicode):
        changes = changes.replace('---','*Emulated Ticket Change*', 1)
        changes = changes.replace('\n- -','\n*Field:*')
        before = changes
        while True:
            after = before.replace('\n  -','\n_From:_', 1)
            after = after.replace('\n  -','\n_To:_', 1)
            if before == after:
                return after
            before = after
    return changes

def copy_ticket_statuses(space1, space2):
    logger.debug('[TicketStatus] Starting')
    statuses1 = space1.get_ticket_statuses()
    statuses2 = space2.get_ticket_statuses()
    missing = []
    for status in statuses1:
        if status.name not in [s.name for s in statuses2]:
            missing.append(status)
        else:
            logger.debug('[TicketStatus] Skipping %s', status.name)
    for status in missing:
        s=space2.create_ticket_status(status)
        logger.debug('[TicketStatus] Created %s',status.name)
    logger.debug('[TicketStatus] Finished')

def copy_ticket_custom_fields(space1, space2):
    logger.debug('[TicketCustomField] Starting')
    fields1 = space1.get_custom_fields()
    fields2 = space2.get_custom_fields()
    missing = []
    for field in fields1:
        if field.title not in [f.title for f in fields2]:
            missing.append(field)
        else:
            logger.debug('[TicketCustomField] Skipping %s',field.title)
    for field in missing:
        space2.create_custom_field(field)
        logger.debug('[TicketCustomField] Created %s',field.title)
    logger.debug('[TicketCustomField] Finished')

def copy_ticket_components(space1, space2):
    logger.debug('[TicketComponent] Starting')
    components1 = space1.get_components()
    components2 = space2.get_components()
    existing_comp_map={}
    for c in components2:
        existing_comp_map[c.name] = c.id
    missing = []
    mapping = {}
    for component in components1:
        if component.name not in [c.name for c in components2]:
            missing.append(component)
        else:
            mapping[component.id] = existing_comp_map[component.name]
            logger.debug('[TicketCustomField] Skipping %s',component.name)
    for component in missing:
        tc=space2.create_component(component)
        logger.debug('[TicketCustomField] Created %s',component.name)
        mapping[component.id] = tc.id
    # Ticket component IDs may differ, return a mapping for new components
    logger.debug('[TicketComponent] Finished')
    return mapping

def copy_milestones(space1, space2):
    logger.debug('[Milestone] Starting')
    milestones1 = space1.get_milestones()
    milestones2 = space2.get_milestones()
    existing_ms_map={}
    for m in milestones2:
        existing_ms_map[m.title] = m.id
    missing = []
    mapping = {}
    for milestone in milestones1:
        if milestone.title not in [m.title for m in milestones2]:
            missing.append(milestone)
        else:
            mapping[milestone.id] = existing_ms_map[milestone.title]
            logger.debug('[Milestone] Skipping %s', milestone.title)
    for milestone in missing:
        ms=space2.create_milestone(milestone)
        mapping[milestone.id] = ms.id
    logger.debug('[Milestone] Finished')
    # Ticket milestone IDs may differ, return a mapping for new milestones
    return mapping

def copy_document(file_id, ticket1, ticket2, auth=None):
    logger.debug('[Document] Starting')
    if not auth:
        return
    from lxml.html import fromstring, submit_form
    import requests
    try:
        olddoc = ticket1.get_document(file_id)
    except AssemblaError:
        logger.debug('[Document] not found %s', file_id)
        return
    login_url = 'https://www.assembla.com/do_login'
    client = requests.session()
    login_form = fromstring(client.get(login_url).content).forms[0]
    login_form.fields['user[login]'] = auth[0]
    login_form.fields['user[password]'] = auth[1]
    login_response = submit_form(login_form, open_http=client.request)
    if login_response.status_code != 200:
        raise AssemblaError('Failed login on file download: ',
                response=login_response.status_code)
    response=client.get(olddoc.url)
    newdoc=ticket2.attach_file(response, olddoc)
    logger.debug('[Document] Attached %s', newdoc.id)
    logger.debug('[Document] Finished')

def copy_ticket_comments(ticket1, ticket2, auth=None):
    logger.debug('[TicketComment] Starting')
    comments = ticket1.get_comments()
    for c in comments:
        c_text = getattr(c, 'comment', None)
        if c.file:
            if auth: # allows for downloading files from www.assembla.com
                copy_document(c.file, ticket1, ticket2, auth)
        else:
            if c_text:
                c = ticket2.create_comment(c)
                logger.debug('[TicketComment] Created %s', c.id)
            else:
                # emulate system comment through regular comment
                c.comment = prettify(c.ticket_changes)
                c = ticket2.create_comment(c)
                logger.debug('[TicketComment] Emulated %s', c.id)
    logger.debug('[TicketComment] Finished')

def copy_ticket(ticket1, space2, component_map, milestone_map, auth=None):
    logger.debug('[Ticket] Starting')
    if ticket1.milestone_id:
        ticket1.milestone_id = milestone_map[ticket1.milestone_id]
    if ticket1.component_id:
        ticket1.component_id = component_map[ticket1.component_id]
    ticket2 = space2.create_ticket(ticket1)
    logger.debug('[Ticket] Created %s', ticket2.id)
    copy_ticket_comments(ticket1, ticket2, auth)
    logger.debug('[Ticket] Finished')
    return ticket2

def check_association_ambivalent(a1, a2, id_map):
    r = False
    if id_map[a1.ticket1_id] == a2.ticket1_id and id_map[a1.ticket2_id] == a2.ticket2_id:
        r = True
    elif id_map[a1.ticket2_id] == a2.ticket1_id and id_map[a1.ticket1_id] == a2.ticket2_id:
        r = True
    return r


def copy_ticket_associations(space1, space2, ticket_map):
    logger.debug('[TicketAssociation] Starting')
    for t2 in space2.get_tickets():
        logger.debug('[TicketAssociation] Processing %s', t2.id)
        t1 = space1.get_ticket(t2.number)
        for ass1 in t1.get_associations():
            # skip if associated ticket not copied
            if ass1.ticket1_id not in ticket_map or \
                    ass1.ticket2_id not in ticket_map:
                logger.debug('[TicketAssociation] Skipping %s', ass1.id)
                continue
            # skip if association already exists
            exists = False
            for ass2 in t2.get_associations():
                exists = check_association_ambivalent(ass1, ass2, ticket_map)
            if exists:
                logger.debug('[TicketAssociation] Skipping %s', ass1.id)
                continue

            ass_t2_id = ass1.ticket2_id
            ass1.ticket1_id = ticket_map[ass1.ticket1_id]
            ass1.ticket2_id = ticket_map[ass1.ticket2_id]
            # fix API glitch
            if t2.id == ticket_map[ass_t2_id]:
                ass1.invert()
            t2.create_association(ass1)
            logger.debug('[TicketAssociation] Associating %s - %s',
                    ass1.ticket1_id, ass1.ticket2_id)
    logger.debug('[TicketAssociation] Finished')

def migrate_space_tickets(space1, space2, ticket_numbers=None, auth=None):
    logger.debug('[Migration] Starting')
    # prepare space
    logger.debug('[Migration] Preparing space')
    copy_ticket_statuses(space1, space2)
    copy_ticket_custom_fields(space1, space2)
    component_map = copy_ticket_components(space1, space2)
    milestone_map = copy_milestones(space1, space2)
    logger.debug('[Migration] Finished preparing space')
    # process tickets
    logger.debug('[Migration] Copying tickets from %s to %s',
            space1.name, space2.name)
    tickets = []
    ticket_mapping = {}
    if ticket_numbers:
        for n in ticket_numbers:
            tickets.append(space1.get_ticket(n))
    else:
        tickets = space1.get_tickets()
    for t in tickets:
        ticket2 = copy_ticket(t, space2, component_map, milestone_map, auth)
        ticket_mapping[t.id] = ticket2.id
    logger.debug('[Migration] Finished copying tickets')
    copy_ticket_associations(space1, space2, ticket_mapping)
    logger.debug('[Migration] Finished')
