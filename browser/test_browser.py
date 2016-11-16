import urwid
import os
import json
import pickle


class TestDetailTextBox(urwid.WidgetWrap):

    def __init__(self, text):
        self.listbox_widget = None
        self.set_text(text)
        super(TestDetailTextBox, self).__init__(self.listbox_widget)

    def set_text(self, text):
        lines = text.split('\n')
        self.listbox_widget = urwid.ListBox([urwid.Text("")]) if self.listbox_widget is None else self.listbox_widget
        line_widgets = self.listbox_widget.body.contents
        for idx in xrange(len(lines)):
            if idx < len(line_widgets):
                line_widgets[idx].set_text(lines[idx])
            else:
                line_widgets.append(urwid.Text(lines[idx]))
        if len(lines) < len(line_widgets):
            for idx in xrange(len(lines), len(line_widgets)):
                line_widgets[idx].set_text("")
        if len(line_widgets):
            self.listbox_widget.set_focus(0)


class TestTreeNode(object):
    def __init__(self, parent, data, name):
        self.parent = parent
        self.raw_data = data
        self.name = name
        self.children = []

    @property
    def fixture_data(self):
        try:
            return self.raw_data['fixtures']
        except TypeError or KeyError:
            return None

    @staticmethod
    def get_node_with_name(start_node, name, force_creation=True):
        node = next((child for child in start_node.children if child.name == name), None)
        if not node and force_creation:
            node = TestTreeNode(parent=start_node, data=None, name=name)
            start_node.children.append(node)
        return node

    def get_node_with_path(self, path, force_creation=True):
        node = self
        for name in path:
            node = self.get_node_with_name(start_node=node, name=name, force_creation=force_creation)
        return node


class FlagTreeWidget(urwid.TreeWidget):
    # apply an attribute to the expand/unexpand icons
    unexpanded_icon = urwid.AttrMap(urwid.TreeWidget.unexpanded_icon, 'dirmark')
    expanded_icon = urwid.AttrMap(urwid.TreeWidget.expanded_icon, 'dirmark')

    def __init__(self, node):
        super(FlagTreeWidget, self).__init__(node=node)
        # insert an extra AttrWrap for our own use
        self._w = urwid.AttrWrap(self._w, None)
        self.flagged = False
        self.update_w()

    def selectable(self):
        return True

    def mouse_event(self, size, event, button, col, row, focus):
        if super(FlagTreeWidget, self).mouse_event(size, event, button, col, row, focus):
            return True
        elif event == 'mouse press' and button == 3:
            self.toggle_flagged()
            return True
        elif event == 'mouse press' and button == 1:
            self.update_test_details()
            return True
        else:
            return False

    def keypress(self, size, key):
        """allow subclasses to intercept keystrokes"""
        key = super(FlagTreeWidget, self).keypress(size, key)
        if key:
            key = self.unhandled_keys(size, key)
        return key

    def unhandled_keys(self, size, key):
        """
        Override this method to intercept keystrokes in subclasses.
        Default behavior: Toggle flagged on space, ignore other keys.
        """
        key = "up" if key == 'u' else key
        key = "down" if key == 'd' else key

        if key == " ":
            self.toggle_flagged()
        elif key == "c":
            self.clear_flagged()
        elif key == "left" and not self.is_leaf:
            self.toggle_expanded()
        elif key == "up" or key == "down":
            self.update_test_details(key)
            # update but do not trap key event
            return key
        else:
            return key

    def update_w(self):
        """Update the attributes of self.widget based on self.flagged.
        """
        if self.flagged:
            self._w.attr = 'flagged'
            self._w.focus_attr = 'flagged focus'
        else:
            self._w.attr = 'body'
            self._w.focus_attr = 'focus'

    def toggle_flagged(self):
        if self.is_leaf:
            self.flagged = not self.flagged
            self.update_w()
        else:
            for child_key in self.get_node().get_child_keys():
                self.get_node().get_child_node(child_key).get_widget().toggle_flagged()

    def clear_flagged(self):
        if self.is_leaf:
            self.flagged = False
            self.update_w()
        else:
            for child_key in self.get_node().get_child_keys():
                self.get_node().get_child_node(child_key).get_widget().clear_flagged()

    def toggle_expanded(self):
        self.expanded = False
        self.update_expanded_icon()

    def update_test_details(self, key=None):
        if key == "up":
            tree_node = self.prev_inorder()
            if tree_node is None:
                return
        elif key == "down":
            tree_node = self.next_inorder()
            if tree_node is None:
                return
        else:
            tree_node = self

        node = tree_node.get_node()
        if node.detail_display_widget is None:
            return
        fixture_data = node.get_value().fixture_data
        if fixture_data:
            text = json.dumps(to_dict(fixture_data), indent=2)
        else:
            text = "No fixture information."
        self.get_node().detail_display_widget.set_text(text)


class TestTreeWidget(FlagTreeWidget):
    """ Display widget for leaf nodes """

    def get_display_text(self):
        return self.get_node().get_value().name


class TestNode(urwid.TreeNode):
    """ Data storage object for leaf nodes """
    def __init__(self, value, parent=None, key=None, depth=None, detail_display_widget=None):
        self.detail_display_widget = detail_display_widget
        super(TestNode, self).__init__(value=value, parent=parent, key=key, depth=depth)

    def load_widget(self):
        return TestTreeWidget(self)


class TestContainerNode(urwid.ParentNode):
    """ Data storage object for interior/parent nodes """
    def __init__(self, value, parent=None, key=None, depth=None, detail_display_widget=None):
        self.detail_display_widget = detail_display_widget
        super(TestContainerNode, self).__init__(value=value, parent=parent, key=key, depth=depth)

    def load_widget(self):
        return TestTreeWidget(self)

    def load_child_keys(self):
        data = self.get_value()
        return range(len(data.children))

    def load_child_node(self, key):
        """Return either an ExampleNode or ExampleParentNode"""
        child_data = self.get_value().children[key]
        child_depth = self.get_depth() + 1
        if child_data.children:
            childclass = TestContainerNode
        else:
            childclass = TestNode
        return childclass(child_data,
                          parent=self,
                          key=key,
                          depth=child_depth,
                          detail_display_widget=self.detail_display_widget
                          )

    def get_selected_items(self, selected=None):
        if not selected:
            selected = []
        for child_key in self.get_child_keys():
            child_node = self.get_child_node(child_key)
            child_widget = child_node.get_widget()
            if not child_widget.is_leaf:
                selected.extend(child_node.get_selected_items())
            if child_widget.flagged:
                selected.append(child_node.get_value().raw_data['original_item'])
        return selected


class TestBrowser:
    palette = [
        ('body', 'black', 'light gray'),
        ('flagged', 'black', 'dark green', ('bold', 'underline')),
        ('focus', 'light gray', 'dark blue', 'standout'),
        ('flagged focus', 'yellow', 'dark cyan',
         ('bold', 'standout', 'underline')),
        ('head', 'yellow', 'black', 'standout'),
        ('foot', 'light gray', 'black'),
        ('key', 'light cyan', 'black', 'underline'),
        ('title', 'white', 'black', 'bold'),
        ('dirmark', 'black', 'dark cyan', 'bold'),
        ('flag', 'dark gray', 'light gray'),
        ('error', 'dark red', 'light gray'),
        ('popbg', 'white', 'dark blue')
    ]

    footer_text = [
        ('title', "Example Data Browser"), "    ",
        ('key', "UP"), ",", ('key', "DOWN"), ",",
        ('key', "PAGE UP"), ",", ('key', "PAGE DOWN"),
        "  ",
        ('key', "SPACE"), "  ",
        ('key', "+"), ",",
        ('key', "-"), "  ",
        ('key', "LEFT"), "  ",
        ('key', "HOME"), "  ",
        ('key', "END"), "  ",
        ('key', "Q"), "  ",
        ('key', "C"), "  "
    ]

    def __init__(self, items):
        self.items = items
        self.test_tree = self.get_test_tree(items=items)
        self.detail_text_box = TestDetailTextBox('meh')
        self.topnode = TestContainerNode(self.test_tree,  detail_display_widget=self.detail_text_box)
        self.listbox = urwid.TreeListBox(urwid.TreeWalker(self.topnode))
        self.listbox.offset_rows = 1
        self.columns = urwid.Columns([('weight', 2, self.listbox), ('weight', 1.3, self.detail_text_box)])
        self.header = urwid.Text("")
        self.footer = urwid.AttrWrap(urwid.Text(self.footer_text), 'foot')
        self.view = urwid.Frame(
            urwid.AttrWrap(self.columns, 'body'),
            header=urwid.AttrWrap(self.header, 'head'),
            footer=self.footer)
        self.loop = None

    def main(self):
        """Run the program."""
        self.loop = urwid.MainLoop(self.view, self.palette, unhandled_input=self.unhandled_input, pop_ups=True)
        self.loop.run()

    @staticmethod
    def unhandled_input(k):
        if k in ('q', 'Q'):
            raise urwid.ExitMainLoop()

    def get_selected_items(self):
        return self.topnode.get_selected_items(selected=None)

    @staticmethod
    def get_test_tree(items):
        if items is None:
            # use pickled test data
            with open(os.path.join(os.path.dirname(__file__), "test_data.pkl"), 'r') as f:
                data = pickle.load(f)
        else:
            # use real data
            data = [process_item(item) for item in items]
        test_tree = build_data_tree(data=data)
        return test_tree


def process_dict(d):
    new_dict = dict()
    for key, value in d.items():
        if value is None:
            continue
        elif isinstance(value, list):
            try:
                value = list(set(value))
            except TypeError:
                # we cannot reduce this list easily leave it be
                pass
        elif isinstance(value, dict):
            value = process_dict(value)
        new_dict[key] = value
    return new_dict


def process_item(item):
    item_data = dict()
    item_data['original_item'] = item
    item_data['name'] = item.name
    item_data['fixtures'] = item.callspec.params if hasattr(item, 'callspec') else {}
    item_data['module'] = item.location[0]
    item_location = item.location[2].split('.')
    if len(item_location) == 1:
        # no class just function
        item_data['class'] = 'No Class Definition'
        item_data['name'] = item_location[0]
    else:
        # This more or less covers all that needs covered
        item_data['class'] = '-'.join(item_location[:-1])
        item_data['name'] = item_location[-1]
    return item_data


def process_fixture_definitions(fixturedefs):
    fixtures = dict()
    for key, value in fixturedefs.iteritems():
        fixtures[key.strip('_')] = value[0].params
    return process_dict(fixtures)


def build_data_tree(data):
    if data:
        tree = TestTreeNode(parent=None, data=None, name='/')
        for datum in data:
            test_branch = datum['module'].split('/')
            test_class = datum['class']
            test_branch.append(test_class)
            test_branch.append(datum['name'])
            node = tree.get_node_with_path(path=test_branch)
            node.raw_data = datum
        return tree
    else:
        return None


def to_dict(obj, class_key=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = to_dict(v, class_key)
        return data
    elif hasattr(obj, "_ast"):
        return to_dict(obj._ast())
    elif hasattr(obj, "__iter__"):
        return [to_dict(v, class_key) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, to_dict(value, class_key))
                     for key, value in obj.__dict__.items() if not callable(value) and not key.startswith('_')])
        if class_key is not None and hasattr(obj, "__class__"):
            data[class_key] = obj.__class__.__name__
        return data
    else:
        return obj



