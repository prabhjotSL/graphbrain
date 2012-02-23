# (c) 2012 GraphBrain Ltd. All rigths reserved.

# Entry point functions & global variables


g = false
newLink = false
draggedNode = false
dragging = false
curTargNode = false
tipVisible = false
lastX = 0
lastY = 0


initInterface = ->
    if error != ''
        $("#tip").html('<div class="error">' + error + '</div>')
        $("#tip").fadeIn "slow", () => 
            tipVisible = true

    $("#nodesDiv").bind "mouseup", (e) =>
        dragging = false
        draggedNode = false

    $("#nodesDiv").bind "mousedown", (e) =>
        dragging = true
        lastX = e.pageX
        lastY = e.pageY
        false

    $("#nodesDiv").bind "mousemove", (e) =>
        if dragging
            deltaX = e.pageX - lastX
            deltaY = e.pageY - lastY
            lastX = e.pageX
            lastY = e.pageY
            g.rotateX(-deltaX * 0.0015)
            g.rotateY(deltaY * 0.0015)
            g.updateView()

        if draggedNode
            draggedNode.moveTo(e.pageX, e.pageY)
            dragging = true


initGraph = ->
    g = new Graph()

    # process super nodes and associated nodes
    for sn in snodes
        sid = sn['id']
        nlist = sn['nodes']
        
        snode = new SNode(sid)

        for nid in nlist
            nod = nodes[nid]
            text = nod['text']
            type = nod['type']
            parentID = nod['parent']
            node = new Node(nid, text, type, snode)
            snode.nodes[nid] = node
            g.nodes[nid] = node

            if (snode.parent == 'unknown') or (parentID == '')
                snode.parent = parentID

        g.snodes[sid] = snode   

    # assign root, parents and subNodes
    for sn in snodes
        sid = sn['id']
        snode = g.snodes[sid]
        parentID = snode.parent
        if parentID == ''
            g.root = snode
            snode.parent = false
        else
            snode.parent = g.nodes[parentID].snode
            g.nodes[parentID].snode.subNodes[g.nodes[parentID].snode.subNodes.length] = snode


    # assign depth and weight
    for key of g.snodes when g.snodes.hasOwnProperty(key)
        snode = g.snodes[key]
        snode.weight = snode.nodes.size()
        if not snode.parent
            snode.depth = 0
        else if snode.parent == g.root
            snode.depth = 1
            snode.weight += subNode.nodes.size() for subNode in snode.subNodes
        else
            snode.depth = 2

    g.genSNodeKeys()

    # process links
    linkID = 0
    for l in links
        orig = ''
        targ = ''
        sorig = ''
        starg = ''
        if 'orig' of l
            orig  = g.nodes[l['orig']]
            sorig = orig.snode
        else
            orig = false
            sorig = g.snodes[l['sorig']]
        if 'targ' of l
            targ  = g.nodes[l['targ']]
            starg = targ.snode
        else
            targ = false
            starg  = g.snodes[l['starg']]
        link = new Link(linkID++, orig, sorig, targ, starg, l['relation'])
        g.links.push(link)
        sorig.links.push(link)
        starg.links.push(link)
    
    halfWidth = window.innerWidth / 2
    halfHeight = window.innerHeight / 2

    g.placeNodes()
    g.placeLinks()
    g.layout(window.innerWidth, window.innerHeight)
    g.updateView()


$ =>
    initInterface()
    initGraph()