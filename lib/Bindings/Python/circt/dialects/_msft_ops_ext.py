#  Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
#  See https://llvm.org/LICENSE.txt for license information.
#  SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

from circt.dialects import hw, msft as _msft
import circt.dialects._hw_ops_ext as _hw_ext
import circt.support as support

import mlir.ir as _ir


class InstanceBuilder(support.NamedValueOpView):
  """Helper class to incrementally construct an instance of a module."""

  def __init__(self,
               module,
               name,
               input_port_mapping,
               *,
               sym_name=None,
               parameters=None,
               target_design_partition=None,
               loc=None,
               ip=None):
    self.module = module
    instance_name = _ir.StringAttr.get(name)
    module_name = _ir.FlatSymbolRefAttr.get(_ir.StringAttr(module.name).value)
    if sym_name:
      sym_name = _ir.StringAttr.get(sym_name)
    pre_args = [instance_name, module_name]
    if parameters is not None:
      parameters = _hw_ext.create_parameters(parameters, module)
    else:
      parameters = []
    post_args = []
    results = module.type.results

    super().__init__(
        _msft.InstanceOp,
        results,
        input_port_mapping,
        pre_args,
        post_args,
        parameters=_ir.ArrayAttr.get(parameters),
        targetDesignPartition=target_design_partition,
        loc=loc,
        ip=ip,
    )

  def create_default_value(self, index, data_type, arg_name):
    type = self.module.type.inputs[index]
    return support.BackedgeBuilder.create(type,
                                          arg_name,
                                          self,
                                          instance_of=self.module)

  def operand_names(self):
    arg_names = _ir.ArrayAttr(self.module.attributes["argNames"])
    arg_name_attrs = map(_ir.StringAttr, arg_names)
    return list(map(lambda s: s.value, arg_name_attrs))

  def result_names(self):
    arg_names = _ir.ArrayAttr(self.module.attributes["resultNames"])
    arg_name_attrs = map(_ir.StringAttr, arg_names)
    return list(map(lambda s: s.value, arg_name_attrs))


class MSFTModuleOp(_hw_ext.ModuleLike):

  def __init__(
      self,
      name,
      input_ports=[],
      output_ports=[],
      parameters: _ir.DictAttr = None,
      file_name: str = None,
      loc=None,
      ip=None,
  ):
    attrs = {"parameters": parameters}
    if parameters is not None:
      attrs["parameters"] = parameters
    else:
      attrs["parameters"] = _ir.DictAttr.get({})
    if file_name is not None:
      attrs["fileName"] = _ir.StringAttr.get(file_name)
    super().__init__(name,
                     input_ports,
                     output_ports,
                     attributes=attrs,
                     loc=loc,
                     ip=ip)

  def instantiate(self, name: str, loc=None, ip=None, **kwargs):
    return InstanceBuilder(self, name, kwargs, loc=loc, ip=ip)

  def add_entry_block(self):
    self.body.blocks.append(*self.type.inputs)
    return self.body.blocks[0]

  @property
  def body(self):
    return self.regions[0]

  @property
  def entry_block(self):
    return self.regions[0].blocks[0]

  @property
  def parameters(self):
    return [
        hw.ParamDeclAttr.get(p.name, _ir.TypeAttr.get(p.attr.type), p.attr)
        for p in _ir.DictAttr(self.attributes["parameters"])
    ]


class MSFTModuleExternOp(_hw_ext.ModuleLike):

  def instantiate(self,
                  name: str,
                  parameters=None,
                  results=None,
                  loc=None,
                  ip=None,
                  **kwargs):
    return InstanceBuilder(self,
                           name,
                           kwargs,
                           sym_name=name,
                           parameters=parameters,
                           loc=loc,
                           ip=ip)


class PhysicalRegionOp:

  def add_bounds(self, bounds):
    existing_bounds = [b for b in _ir.ArrayAttr(self.attributes["bounds"])]
    existing_bounds.append(bounds)
    new_bounds = _ir.ArrayAttr.get(existing_bounds)
    self.attributes["bounds"] = new_bounds


class InstanceOp:

  @property
  def moduleName(self):
    return _ir.FlatSymbolRefAttr(self.attributes["moduleName"])


class EntityExternOp:

  @staticmethod
  def create(symbol, metadata=""):
    symbol_attr = support.var_to_attribute(symbol)
    metadata_attr = support.var_to_attribute(metadata)
    return _msft.EntityExternOp(symbol_attr, metadata_attr)


class InstanceHierarchyOp:

  @staticmethod
  def create(root_mod, instance_name=None):
    hier = _msft.InstanceHierarchyOp(root_mod, instName=instance_name)
    hier.body.blocks.append()
    return hier

  @property
  def top_module_ref(self):
    return self.attributes["topModuleRef"]


class DynamicInstanceOp:

  @staticmethod
  def create(name_ref):
    inst = _msft.DynamicInstanceOp(name_ref)
    inst.body.blocks.append()
    return inst

  @property
  def instance_path(self):
    path = []
    next = self
    while isinstance(next, DynamicInstanceOp):
      path.append(next.attributes["instanceRef"])
      next = next.operation.parent.opview
    path.reverse()
    return _ir.ArrayAttr.get(path)

  @property
  def instanceRef(self):
    return self.attributes["instanceRef"]


class PDPhysLocationOp:

  @property
  def loc(self):
    return _msft.PhysLocationAttr(self.attributes["loc"])
