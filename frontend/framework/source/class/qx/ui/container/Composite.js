/* ************************************************************************

   qooxdoo - the new era of web development

   http://qooxdoo.org

   Copyright:
     2004-2008 1&1 Internet AG, Germany, http://www.1und1.de

   License:
     LGPL: http://www.gnu.org/licenses/lgpl.html
     EPL: http://www.eclipse.org/org/documents/epl-v10.php
     See the LICENSE file in the project's top-level directory for details.

   Authors:
     * Sebastian Werner (wpbasti)
     * Fabian Jakobs (fjakobs)

************************************************************************ */

qx.Class.define("qx.ui.container.Composite",
{
  extend : qx.ui.core.Widget,
  include : [ qx.ui.core.MChildrenHandling, qx.ui.core.MLayoutHandling ],



  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */

  /**
   * @param layout {qx.ui.layout.Abstract} A layout instance to use to
   *   place widgets on the screen.
   */
  construct : function(layout)
  {
    this.base(arguments);

    if (layout != null) {
      this._setLayout(layout);
    }
  },




  /*
  *****************************************************************************
     DEFER
  *****************************************************************************
  */

  defer : function(statics, members)
  {
    qx.ui.core.MChildrenHandling.remap(members);
    qx.ui.core.MLayoutHandling.remap(members);
  }
})