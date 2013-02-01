from assembla.error import AssemblaError
import logging
import re
from copy import deepcopy

logger = logging.getLogger('ATMT')

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

def remap_references(line, number_map):
    if isinstance(line, str) or isinstance(line, unicode):
        refs = {int(ref) for ref in re.findall(r'#([0-9]+)', line)}
        for r in refs:
            nm = number_map.get(r, 'not-copied')
            line = line.replace('#%s' % r, '#%s' % nm)
    else:
        logger.debug('[ReferenceRemap] Skipping unknown type: %s, line: %s', type(line), line)
    return line

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
        logger.debug('[TicketStatus] Creating %s',status.name)
        s=space2.create_ticket_status(status)
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
        logger.debug('[TicketCustomField] Creating %s',field.title)
        space2.create_custom_field(field)
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
            logger.debug('[TicketComponent] Skipping %s',component.name)
    logger.debug('[TicketComponent] Found %s missing components: %s',
        len(missing), ', '.join([c.name for c in missing]))
    for component in missing:
        logger.debug('[TicketComponent] Creating %s',component.name)
        tc=space2.create_component(component)
        logger.debug('[TicketComponent] Created with id: %s', tc.id)
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
        logger.debug('[Milestone] Creating %s', milestone.title)
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
    logger.debug('[Document] Attaching %s', olddoc.name)
    newdoc=ticket2.attach_file(response, olddoc)
    logger.debug('[Document] Attached with id: %s', newdoc.id)
    logger.debug('[Document] Finished')

def copy_ticket_comments(ticket1, ticket2, number_map, auth=None):
    logger.debug('[TicketComment] Starting')
    comments = ticket1.get_comments()
    for c in comments:
        c_text = getattr(c, 'comment', None)
        if c.file:
            if auth: # allows for downloading files from www.assembla.com
                copy_document(c.file, ticket1, ticket2, auth)
        else:
            if c_text:
                c.comment = remap_references(c.comment, number_map)
                logger.debug('[TicketComment] Creating for %s', c.id)
                c = ticket2.create_comment(c)
                logger.debug('[TicketComment] Created %s', c.id)
            else:
                # emulate system comment through regular comment
                c.comment = prettify(c.ticket_changes)
                logger.debug('[TicketComment] Emulating for %s', c.id)
                c = ticket2.create_comment(c)
                logger.debug('[TicketComment] Emulated %s', c.id)
    logger.debug('[TicketComment] Finished')

def copy_ticket(ticket1, space2, component_map, milestone_map,
        number_map, auth=None):
    logger.debug('[Ticket] Starting')
    tcopy = deepcopy(ticket1)
    if tcopy.milestone_id:
        tcopy.milestone_id = milestone_map[tcopy.milestone_id]
    if tcopy.component_id:
        tcopy.component_id = component_map[tcopy.component_id]
    tcopy.number = number_map[tcopy.number]
    tcopy.description = remap_references(tcopy.description, number_map)
    logger.debug('[Ticket] Creating ticket number %s', tcopy.number)
    ticket2 = space2.create_ticket(tcopy)
    logger.debug('[Ticket] Created with id %s', ticket2.id)
    try:
        copy_ticket_comments(ticket1, ticket2, number_map, auth)
    except AssemblaError, e:
        logger.debug("[Ticket] Comments copy failed")
        space2.delete_ticket(ticket2.number)
        logger.debug("[Ticket] Deleted ticket %s", ticket2.number)
        raise e
    logger.debug('[Ticket] Finished')
    return ticket2

def check_association_ambivalent(a1, a2, id_map):
    r = False
    if id_map[a1.ticket1_id] == a2.ticket1_id and id_map[a1.ticket2_id] == a2.ticket2_id:
        r = True
    elif id_map[a1.ticket2_id] == a2.ticket1_id and id_map[a1.ticket1_id] == a2.ticket2_id:
        r = True
    return r


def copy_ticket_associations(space1, space2, id_map, number_map):
    logger.debug('[TicketAssociation] Starting')
    for n in number_map:
        t2 = space2.get_ticket(number_map[n])
        logger.debug('[TicketAssociation] Processing %s', t2.id)
        t1 = space1.get_ticket(n)
        for ass1 in t1.get_associations():
            # skip if associated ticket not copied
            if ass1.ticket1_id not in id_map or \
                    ass1.ticket2_id not in id_map:
                logger.debug('[TicketAssociation] Skipping %s', ass1.id)
                continue
            # skip if association already exists
            exists = False
            for ass2 in t2.get_associations():
                exists = check_association_ambivalent(ass1, ass2, id_map)
            if exists:
                logger.debug('[TicketAssociation] Skipping %s', ass1.id)
                continue

            ass_t2_id = ass1.ticket2_id
            ass1.ticket1_id = id_map[ass1.ticket1_id]
            ass1.ticket2_id = id_map[ass1.ticket2_id]
            # fix API glitch
            if t2.id == id_map[ass_t2_id]:
                ass1.invert()
            logger.debug('[TicketAssociation] Associating %s - %s',
                    ass1.ticket1_id, ass1.ticket2_id)
            t2.create_association(ass1)
            logger.debug('[TicketAssociation] Associated')
    logger.debug('[TicketAssociation] Finished')

def prepare_space_fields(space1, space2):
    logger.debug('[Migration] Preparing space')
    copy_ticket_statuses(space1, space2)
    copy_ticket_custom_fields(space1, space2)
    component_map = copy_ticket_components(space1, space2)
    milestone_map = copy_milestones(space1, space2)
    logger.debug('[Migration] Finished preparing space')
    return (component_map, milestone_map)

def check_ticket_numbers(space1, space2, ticket_numbers, renumber=False):
    logger.debug('[TicketNumbers] Starting sanity check (may take a while)')
    tickets = []
    if ticket_numbers:
        for n in ticket_numbers:
            tickets.append(space1.get_ticket(n))
    else:
        tickets = space1.get_tickets()
    if not renumber:
        for t in tickets:
            logger.debug('[TicketNumbers] Checking ticket %s' % t.number)
            try:
                t2 = space2.get_ticket(t.number)
                if t2:
                    logger.debug('[TicketNumbers] Ticket %s exists' % t.number)
                    return None, None
            except AssemblaError, e:
                if not e.reason.startswith("Couldn't find Ticket"):
                    raise e
        else:
            logger.debug('[TicketNumbers] Finished sanity check')
            return tickets, dict(zip(ticket_numbers, ticket_numbers))
    temp_ticket = deepcopy(tickets[0])
    temp_ticket.number = None
    temp_ticket = space2.create_ticket(temp_ticket)
    start = temp_ticket.number
    end = start+len(tickets)
    ticket_number_map = dict(zip([t.number for t in tickets], range(start,end)))
    temp_ticket.destroy()
    logger.debug('[TicketNumbers] Finished sanity check')
    return tickets, ticket_number_map

def copy_tickets(tickets, space1, space2, component_map, milestone_map,
        number_map, auth=None):
    logger.debug('[Migration] Starting Ticket copy from %s to %s',
            space1.name, space2.name)
    ticket_id_map = {}
    new_tickets_id_number_map = {}
    for t in tickets:
        try:
            ticket2 = copy_ticket(t, space2, component_map, milestone_map, number_map, auth=auth)
        except AssemblaError, e:
            logger.debug("[Migration] Got an AssemblaError, body:\n\n%s", e.response.content)
            logger.debug("[Migration] Revertintg migration")
            for tid, tnum in new_tickets_id_number_map.items():
                space2.delete_ticket(tnum)
                logger.debug("[Migration] Deleted ticket %s", tnum)
            else:
                break
        ticket_id_map[t.id] = ticket2.id
        new_tickets_id_number_map[ticket2.id] = ticket2.number
    logger.debug('[Migration] Finished Ticket copy')
    return ticket_id_map

def migrate_tickets(space1, space2, ticket_numbers=None, auth=None,
        renumber=False):
    logger.debug('[Migration] Starting')
    component_map, milestone_map = prepare_space_fields(space1, space2)
    tickets, number_map = check_ticket_numbers(space1, space2, ticket_numbers,
            renumber=renumber)
    if tickets == None:
        logger.debug('[Migration] Ticket numbers failed sanity check, exiting')
        return None
    ticket_id_map = copy_tickets(tickets, space1, space2, component_map,
            milestone_map, number_map, auth=auth)
    copy_ticket_associations(space1, space2, ticket_id_map, number_map)
    logger.debug('[Migration] Finished')
    return number_map
