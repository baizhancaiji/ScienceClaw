# 材料科学与化学领域工具最终清单

**分析范围**: ToolUniverse全部 1945 个工具
**相关工具**: 210 个（已排除物理和生命科学类工具）

## 1. 统计概览

### 1.1 按大类统计

| 大类 | 工具数量 | 百分比 |
|------|----------|--------|
| 材料科学 | 4 | 1.9% |
| 化学 | 29 | 13.8% |
| 通用工具 | 177 | 84.3% |
| **总计** | **210** | **100%** |

### 1.2 可用性统计

| 可用性状态 | 工具数量 | 百分比 |
|------------|----------|--------|
| 可用 | 206 | 98.1% |
| 需要API密钥 | 2 | 1.0% |
| 需要登录 | 2 | 1.0% |

### 1.3 各大类子分类统计

#### 材料科学

| 子类 | 工具数量 | 占比 | 可用性分布 |
|------|----------|------|------------|
| 计算材料 | 4 | 100.0% | 可用: 4 |

#### 化学

| 子类 | 工具数量 | 占比 | 可用性分布 |
|------|----------|------|------------|
| 化学信息学 | 24 | 82.8% | 可用: 23, 需要API密钥: 1 |
| 化学数据库 | 2 | 6.9% | 可用: 2 |
| 计算化学 | 1 | 3.4% | 可用: 1 |
| 光谱分析 | 1 | 3.4% | 可用: 1 |
| 化学反应与合成 | 1 | 3.4% | 可用: 1 |

#### 通用工具

| 子类 | 工具数量 | 占比 | 可用性分布 |
|------|----------|------|------------|
| Python包信息 | 91 | 51.4% | 可用: 91 |
| 其他通用工具 | 52 | 29.4% | 可用: 51, 需要登录: 1 |
| 学术文献与引用 | 7 | 4.0% | 可用: 7 |
| 网页与搜索 | 6 | 3.4% | 可用: 6 |
| 文件与执行 | 6 | 3.4% | 可用: 6 |
| 统计分析 | 5 | 2.8% | 可用: 3, 需要API密钥: 1, 需要登录: 1 |
| 文档处理 | 4 | 2.3% | 可用: 4 |
| 数据存储与检索 | 3 | 1.7% | 可用: 3 |
| 知识图谱与本体 | 2 | 1.1% | 可用: 2 |
| 机器学习 | 1 | 0.6% | 可用: 1 |

## 2. 各大类工具详细清单

### 2.1 材料科学 (4个工具)

#### 计算材料 (4个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| get_deepchem_info | get_deepchem_info | 获取关于DeepChem的全面信息——将先进AI/ML技术应用于药物发现、材料科学和量子化学的开源工具包 | 可用 | DeepChem材料科学AI工具包 |
| get_dscribe_info | get_dscribe_info | 获取关于DScribe的全面信息——用于生成材料和分子机器学习描述符的库 | 可用 | 材料机器学习描述符库 |
| get_schnetpack_info | get_schnetpack_info | 获取SchNetPack的全面信息 - 基于PyTorch构建的分子和材料深度学习工具箱 | 可用 | 分子和材料深度学习工具箱 |
| get_torch_geometric_info | get_torch_geometric_info | 获取PyTorch Geometric的全面信息 - 一个广泛应用于分子和材料科学的高性能图神经网络库 | 可用 | 图神经网络库 |

### 2.2 化学 (29个工具)

#### 化学信息学 (24个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| ChEMBL_get_activity | ChEMBL_get_activity | 通过活动ID获取特定活性的详细信息。活动ID可从ChEMBL_search_activities或ChEMBL_get_target_activities的结果中找到。 | 可用 | 匹配化学信息学关键词 |
| ChEMBL_get_assay | ChEMBL_get_assay | 通过ChEMBL测定ID获取测定的详细信息。要查找测定ID，请使用ChEMBL_search_assays或ChEMBL_get_target_assays。 | 可用 | 匹配化学信息学关键词 |
| ChEMBL_get_compound_record | ChEMBL_get_compound_record | 通过ChEMBL化合物记录ID获取化合物记录信息。 | 可用 | 匹配化学信息学关键词 |
| ChEMBL_get_molecule | ChEMBL_get_molecule | 通过ChEMBL ID获取分子的详细信息。返回分子属性、结构、同义词和相关数据。 | 可用 | 匹配化学信息学关键词 |
| ChEMBL_get_molecule_image | ChEMBL_get_molecule_image | 通过ChEMBL ID获取分子结构图像（SVG或PNG格式）。返回图像URL和元数据。 | 可用 | 匹配化学信息学关键词 |
| ChEMBL_get_molecule_targets | ChEMBL_get_molecule_targets | 通过ChEMBL ID获取与分子相关的所有靶标。返回具有该分子活性数据的靶标。 | 可用 | 匹配化学信息学关键词 |
| Chem_sa_score | Chem_sa_score | 使用RDKit SA_Score贡献模块计算SMILES字符串分子的合成可及性（SA）分数。该算法通过类药化合物的片段频率统计编码合成复杂度。分数范围从1（最小合成难度，简单构建块）到10（高度复杂、... | 可用 | 匹配化学信息学关键词 |
| Enamine_get_compound | Enamine_get_compound | 通过Enamine ID获取化合物详情。返回结构、可用性、价格及订购信息。 | 可用 | 匹配化学信息学关键词 |
| LipidMaps_get_compound_by_id | LipidMaps_get_compound_by_id | 通过LIPID MAPS ID(LMID)获取脂质结构与分类信息。返回完整记录包括名称、分子式、精确质量、SMILES、InChI及KEGG/HMDB/ChEBI/PubChem交叉引用。例如：'LM... | 可用 | 匹配化学信息学关键词 |
| Mcule_lookup_compound | Mcule_lookup_compound | 通过SMILES、InChIKey或Mcule ID在Mcule平台查找可购买化合物。Mcule整合了3000多万个来自多个化学供应商的化合物。返回匹配的Mcule ID和SMILES结构。可接受任何... | 需要API密钥 | 匹配化学信息学关键词 |
| PubChemTox_get_ghs_classification | PubChemTox_get_ghs_classification | 从PubChem获取化合物的GHS(全球统一制度)危害分类。返回危害象形图、信号词(危险/警告)、GHS危害声明(如H301'吞咽有毒')和预防声明。GHS是联合国识别危险化学品的系统。可通过PubC... | 可用 | 匹配化学信息学关键词 |
| PubChem_get_CID_by_SMILES | PubChem_get_CID_by_SMILES | 通过SMILES字符串检索对应的CID列表。 | 可用 | 匹配化学信息学关键词 |
| PubChem_get_associated_patents_by_CID | PubChem_get_associated_patents_by_CID | 获取与特定化合物CID关联的专利列表。 | 可用 | 匹配化学信息学关键词 |
| PubChem_get_compound_2D_image_by_CID | PubChem_get_compound_2D_image_by_CID | 通过CID获取化合物的二维结构图（PNG格式）。 | 可用 | 匹配化学信息学关键词 |
| PubChem_get_compound_synonyms_by_CID | PubChem_get_compound_synonyms_by_CID | 通过CID获取化合物的完整同义词列表。 | 可用 | 匹配化学信息学关键词 |
| ZINC_get_compound | ZINC_get_compound | 通过ZINC ID获取化合物的详细信息，包括SMILES结构、分子性质及供应商/目录可用性。返回供应商列表及最佳采购层级。在ZINC_search_compounds后使用以获取完整数据。 | 可用 | 匹配化学信息学关键词 |
| eMolecules_get_compound | eMolecules_get_compound | 通过eMolecules ID获取化合物详细信息。返回结构、供应商、价格和库存信息。 | 可用 | 匹配化学信息学关键词 |
| eMolecules_get_vendors | eMolecules_get_vendors | 通过SMILES获取化合物的供应商列表。返回供应商名称、价格和库存信息。对化合物采购和成本比较至关重要。 | 可用 | 匹配化学信息学关键词 |
| get_chem_comp_audit_info | get_chem_comp_audit_info | 获取化学组分的审计历史：操作类型、日期、详情、序号和处理站点。 | 可用 | 匹配化学信息学关键词 |
| get_chem_comp_charge_and_ambiguity | get_chem_comp_charge_and_ambiguity | 检索化学组分的形式电荷和歧义标志。 | 可用 | 匹配化学信息学关键词 |
| get_chembl_webresource_client_info | get_chembl_webresource_client_info | 获取chembl-webresource-client包的信息。ChEMBL网络服务的Python客户端 | 可用 | 匹配化学信息学关键词 |
| get_pubchempy_info | get_pubchempy_info | 获取pubchempy包的信息。PubChem REST API的Python接口 | 可用 | 匹配化学信息学关键词 |
| visualize_molecule_2d | visualize_molecule_2d | 使用RDKit可视化2D分子结构。支持SMILES、InChI、分子名称及多种输出格式（包括PNG、SVG和交互式HTML）。前提条件：需安装'rdkit'包（安装命令：pip install too... | 可用 | 匹配化学信息学关键词 |
| visualize_molecule_3d | visualize_molecule_3d | 使用RDKit和py3Dmol可视化3D分子结构。支持SMILES、MOL文件、SDF内容以及各种可视化样式，具有交互式3D查看功能。 | 可用 | 匹配化学信息学关键词 |

#### 化学数据库 (2个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| Enamine_get_libraries | Enamine_get_libraries | 获取Enamine可用化合物库信息，包括REAL数据库、构建模块、筛选化合物和专用库(片段库、共价化合物库等)。 | 可用 | 匹配化学数据库关键词 |
| Mcule_get_database | Mcule_get_database | 通过ID获取特定Mcule化合物数据库文件的详细信息。返回数据库名称、描述、条目数、最后更新日期及带校验和的下载文件链接。已知数据库ID：1(Mcule完整库，1.39亿+化合物)、2(Mcule现货... | 可用 | 匹配化学数据库关键词 |

#### 计算化学 (1个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| get_pyscf_info | get_pyscf_info | 获取关于PySCF的全面信息——一个基于Python的多功能量子化学计算框架 | 可用 | 匹配计算化学关键词 |

#### 光谱分析 (1个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| get_altair_info | get_altair_info | 获取altair包的信息。声明式统计可视化库 | 可用 | 匹配光谱分析关键词 |

#### 化学反应与合成 (1个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| MetaCyc_get_reaction | MetaCyc_get_reaction | 通过反应ID获取MetaCyc反应的详细信息。返回包含底物、产物、酶及反应页面URL的反应数据。 | 可用 | 匹配化学反应关键词 |

### 2.3 通用工具 (177个工具)

#### Python包信息 (91个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| get_albumentations_info | get_albumentations_info | 获取albumentations包的信息。快速图像增强库 | 可用 | Python包信息工具 |
| get_ase_info | get_ase_info | 获取关于ASE(原子模拟环境)的全面信息——用于构建、运行和分析原子模拟的工具包 | 可用 | Python包信息工具 |
| get_bokeh_info | get_bokeh_info | 获取bokeh包的信息。现代网页浏览器交互式可视化库 | 可用 | Python包信息工具 |
| get_brian2_info | get_brian2_info | 获取brian2包的信息。脉冲神经网络模拟器 | 可用 | Python包信息工具 |
| get_cartopy_info | get_cartopy_info | 获取cartopy包的信息。地图投影与地理空间数据处理 | 可用 | Python包信息工具 |
| get_catboost_info | get_catboost_info | 获取关于catboost包的信息。高性能梯度提升库 | 可用 | Python包信息工具 |
| get_cftime_info | get_cftime_info | 获取cftime包的信息。来自netcdf4-python的时间处理功能 | 可用 | Python包信息工具 |
| get_cobra_info | get_cobra_info | 获取关于COBRApy的全面信息——基于约束的代谢建模工具 | 可用 | Python包信息工具 |
| get_cobrapy_info | get_cobrapy_info | 获取关于COBRApy的全面信息——基于约束的代谢建模工具 | 可用 | Python包信息工具 |
| get_cooler_info | get_cooler_info | 获取关于Cooler的综合信息 - 稀疏Hi-C接触矩阵存储 | 可用 | Python包信息工具 |
| get_cryosparc_tools_info | get_cryosparc_tools_info | 获取cryosparc-tools的全面信息——CryoSPARC冷冻电镜处理接口 | 可用 | Python包信息工具 |
| get_cupy_info | get_cupy_info | 获取关于cupy包的信息。基于CUDA加速的NumPy兼容数组库 | 可用 | Python包信息工具 |
| get_cyvcf2_info | get_cyvcf2_info | 获取关于cyvcf2的全面信息——快速处理VCF/BCF文件的工具 | 可用 | Python包信息工具 |
| get_dask_info | get_dask_info | 获取关于dask包的信息。支持任务调度的并行计算 | 可用 | Python包信息工具 |
| get_datamol_info | get_datamol_info | 获取datamol包的信息。简化分子操作的工具 | 可用 | Python包信息工具 |
| get_datashader_info | get_datashader_info | 获取datashader包的信息。用于创建大型数据集有意义可视化的图形管道系统 | 可用 | Python包信息工具 |
| get_dendropy_info | get_dendropy_info | 获取关于dendropy包的信息。Python包：dendropy | 可用 | Python包信息工具 |
| get_descriptastorus_info | get_descriptastorus_info | 获取关于Descriptastorus的全面信息——分子描述符计算工具 | 可用 | Python包信息工具 |
| get_diffdock_info | get_diffdock_info | 获取关于DiffDock的全面信息——基于扩散模型的分子对接工具 | 可用 | Python包信息工具 |
| get_elephant_info | get_elephant_info | 获取elephant包的信息。电生理分析工具包 | 可用 | Python包信息工具 |
| get_faiss_info | get_faiss_info | 获取Faiss的全面信息 - 高效的相似性搜索和聚类工具 | 可用 | Python包信息工具 |
| get_fanc_info | get_fanc_info | 获取FAN-C的全面信息——核接触分析框架 | 可用 | Python包信息工具 |
| get_flask_info | get_flask_info | 获取Flask的全面信息——轻量级WSGI Web应用框架 | 可用 | Python包信息工具 |
| get_geopandas_info | get_geopandas_info | 获取geopandas包的信息。地理空间数据操作与分析 | 可用 | Python包信息工具 |
| get_h5py_info | get_h5py_info | 获取关于h5py的综合信息 - Python的HDF5接口 | 可用 | Python包信息工具 |
| get_hmmlearn_info | get_hmmlearn_info | 获取关于hmmlearn的全面信息——Python中的隐马尔可夫模型库 | 可用 | Python包信息工具 |
| get_holoviews_info | get_holoviews_info | 获取holoviews包的信息。Python声明式数据可视化工具 | 可用 | Python包信息工具 |
| get_igraph_info | get_igraph_info | 获取关于igraph的全面信息——网络分析与可视化工具 | 可用 | Python包信息工具 |
| get_imageio_info | get_imageio_info | 获取imageio包的信息。用于读写图像数据的Python库 | 可用 | Python包信息工具 |
| get_imbalanced_learn_info | get_imbalanced_learn_info | 获取关于imbalanced-learn包的信息。用于不平衡数据集学习的Python工具箱 | 可用 | Python包信息工具 |
| get_joblib_info | get_joblib_info | 获取关于joblib包的信息。轻量级Python函数流水线工具 | 可用 | Python包信息工具 |
| get_lifelines_info | get_lifelines_info | 获取关于lifelines的全面信息——Python生存分析工具 | 可用 | Python包信息工具 |
| get_lightgbm_info | get_lightgbm_info | 获取关于lightgbm包的信息。快速梯度提升框架 | 可用 | Python包信息工具 |
| get_loompy_info | get_loompy_info | 获取关于loompy的全面信息 - 大型组学数据集高效存储工具 | 可用 | Python包信息工具 |
| get_mageck_info | get_mageck_info | 获取关于MAGeCK的全面信息 - CRISPR筛选分析工具包 | 可用 | Python包信息工具 |
| get_matplotlib_info | get_matplotlib_info | 获取关于Matplotlib的全面信息——Python综合可视化库 | 可用 | Python包信息工具 |
| get_mne_info | get_mne_info | 获取mne包的信息。MEG和EEG数据分析 | 可用 | Python包信息工具 |
| get_molfeat_info | get_molfeat_info | 获取molfeat包的信息。简单可靠的分子特征化工具 | 可用 | Python包信息工具 |
| get_molvs_info | get_molvs_info | 获取molvs包的信息——分子验证与标准化工具 | 可用 | Python包信息工具 |
| get_mordred_info | get_mordred_info | 获取mordred包的信息。分子描述符计算器 | 可用 | Python包信息工具 |
| get_msprime_info | get_msprime_info | 获取关于msprime的全面信息 - 溯祖模拟框架 | 可用 | Python包信息工具 |
| get_neo_info | get_neo_info | 获取neo包的信息。电生理数据的表示 | 可用 | Python包信息工具 |
| get_netcdf4_info | get_netcdf4_info | 获取netcdf4包的信息。Python对netCDF C库的接口 | 可用 | Python包信息工具 |
| get_networkx_info | get_networkx_info | 获取关于NetworkX的全面信息 - 网络分析库 | 可用 | Python包信息工具 |
| get_nglview_info | get_nglview_info | 获取nglview包的信息——用于分子可视化的Jupyter组件 | 可用 | Python包信息工具 |
| get_nilearn_info | get_nilearn_info | 获取nilearn包的信息。神经影像的机器学习 | 可用 | Python包信息工具 |
| get_numba_info | get_numba_info | 获取Numba的全面信息——Python即时编译器 | 可用 | Python包信息工具 |
| get_numpy_info | get_numpy_info | 获取关于NumPy的综合信息 - Python科学计算基础包 | 可用 | Python包信息工具 |
| get_openbabel_info | get_openbabel_info | 获取关于OpenBabel的全面信息——化学格式转换与分析工具 | 可用 | Python包信息工具 |
| get_opencv_info | get_opencv_info | 获取关于OpenCV-Python的全面信息——计算机视觉库 | 可用 | Python包信息工具 |
| get_optlang_info | get_optlang_info | 获取关于optlang数学编程优化语言的全面信息 | 可用 | Python包信息工具 |
| get_optuna_info | get_optuna_info | 获取关于optuna包的信息。超参数优化框架 | 可用 | Python包信息工具 |
| get_pandas_info | get_pandas_info | 获取关于pandas的综合信息 - Python强大的数据结构和数据分析工具 | 可用 | Python包信息工具 |
| get_patsy_info | get_patsy_info | 获取关于patsy包的信息。用于描述统计模型的Python库 | 可用 | Python包信息工具 |
| get_pillow_info | get_pillow_info | 获取pillow包的信息。Python Imaging Library的分支 | 可用 | Python包信息工具 |
| get_plotly_info | get_plotly_info | 获取plotly包的信息。Python交互式绘图库 | 可用 | Python包信息工具 |
| get_pyfaidx_info | get_pyfaidx_info | 获取关于pyfaidx的全面信息——高效的FASTA文件索引和随机访问工具 | 可用 | Python包信息工具 |
| get_pykalman_info | get_pykalman_info | 获取关于PyKalman的全面信息 - 卡尔曼滤波和平滑工具 | 可用 | Python包信息工具 |
| get_pymassspec_info | get_pymassspec_info | 获取关于PyMassSpec的全面信息——质谱数据分析工具 | 可用 | Python包信息工具 |
| get_pymed_info | get_pymed_info | 获取关于PyMed的全面信息 - Python版PubMed访问工具 | 可用 | Python包信息工具 |
| get_pymzml_info | get_pymzml_info | 获取pymzML的全面信息 - 质谱mzML文件解析器 | 可用 | Python包信息工具 |
| get_pyrosetta_info | get_pyrosetta_info | 获取pyrosetta包的信息——Rosetta大分子建模套件的Python接口 | 可用 | Python包信息工具 |
| get_pysam_info | get_pysam_info | 获取关于pysam的全面信息——SAM/BAM/CRAM文件接口 | 可用 | Python包信息工具 |
| get_pyscreener_info | get_pyscreener_info | 获取关于PyScreener的全面信息 - Python高通量虚拟筛选工具 | 可用 | Python包信息工具 |
| get_pytdc_info | get_pytdc_info | 获取关于PyTDC的全面信息——Python版治疗数据公共库 | 可用 | Python包信息工具 |
| get_pytorch_info | get_pytorch_info | 获取PyTorch的全面信息 - 一个开源的机器学习框架 | 可用 | Python包信息工具 |
| get_pyvis_info | get_pyvis_info | 获取pyvis包的信息。Python网络可视化库 | 可用 | Python包信息工具 |
| get_qutip_info | get_qutip_info | 获取关于qutip包的信息。Python量子工具箱 | 可用 | Python包信息工具 |
| get_rasterio_info | get_rasterio_info | 获取关于rasterio包的信息。地理空间栅格数据访问工具 | 可用 | Python包信息工具 |
| get_rdkit_info | get_rdkit_info | 获取关于RDKit的全面信息——化学信息学与机器学习工具包 | 可用 | Python包信息工具 |
| get_reportlab_info | get_reportlab_info | 获取关于ReportLab的全面信息——PDF生成库 | 可用 | Python包信息工具 |
| get_requests_info | get_requests_info | 获取关于Requests的全面信息 - Python人性化HTTP库 | 可用 | Python包信息工具 |
| get_ruptures_info | get_ruptures_info | 获取关于ruptures的全面信息 - 变点检测库 | 可用 | Python包信息工具 |
| get_scholarly_info | get_scholarly_info | 获取关于scholarly的全面信息 - Google学术数据检索工具 | 可用 | Python包信息工具 |
| get_scikit_image_info | get_scikit_image_info | 获取关于scikit-image的全面信息——Python图像处理库 | 可用 | Python包信息工具 |
| get_scikit_learn_info | get_scikit_learn_info | 获取scikit-learn的全面信息 - 用于预测性数据分析的简单高效工具 | 可用 | Python包信息工具 |
| get_scipy_info | get_scipy_info | 获取关于SciPy的综合信息 - 科学计算基础算法 | 可用 | Python包信息工具 |
| get_skopt_info | get_skopt_info | 获取关于skopt包的信息。Scikit-Optimize：基于序列模型的优化工具 | 可用 | Python包信息工具 |
| get_statsmodels_info | get_statsmodels_info | 获取statsmodels的全面信息 - 统计建模和计量经济学工具 | 可用 | Python包信息工具 |
| get_sympy_info | get_sympy_info | 获取关于SymPy符号数学库的全面信息 | 可用 | Python包信息工具 |
| get_target_cofactor_info | get_target_cofactor_info | 检索给定靶标的核心辅因子信息，包括辅因子ID、作用机制、文献引用和资源元数据。 | 可用 | Python包信息工具 |
| get_tiledb_info | get_tiledb_info | 获取关于TileDB的综合信息 - 现代阵列数据库 | 可用 | Python包信息工具 |
| get_tool_info | get_tool_info | 获取可配置详细级别的工具信息。支持单个工具（字符串）或多个工具（列表）。使用detail_level='description'仅获取描述字段，或detail_level='full'获取包括参数模式... | 可用 | Python包信息工具 |
| get_tqdm_info | get_tqdm_info | 获取关于tqdm的综合信息 - Python快速进度条 | 可用 | Python包信息工具 |
| get_trackpy_info | get_trackpy_info | 获取trackpy的全面信息——Python粒子追踪工具包 | 可用 | Python包信息工具 |
| get_tskit_info | get_tskit_info | 获取tskit的全面信息——群体遗传学的树序列工具包 | 可用 | Python包信息工具 |
| get_umap_learn_info | get_umap_learn_info | 获取UMAP-learn的全面信息 - 降维技术 | 可用 | Python包信息工具 |
| get_xarray_info | get_xarray_info | 获取关于xarray包的信息。Python中的N维标记数组和数据集 | 可用 | Python包信息工具 |
| get_xesmf_info | get_xesmf_info | 获取关于xesmf包的信息。地理空间数据通用重网格工具 | 可用 | Python包信息工具 |
| get_xgboost_info | get_xgboost_info | 获取关于xgboost包的信息。优化的梯度提升框架 | 可用 | Python包信息工具 |
| get_zarr_info | get_zarr_info | 获取关于zarr包的信息。支持分块压缩的N维数组 | 可用 | Python包信息工具 |

#### 其他通用工具 (52个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| ADA_get_standards_section | ADA_get_standards_section | 通过PMID获取特定ADA护理标准章节的详细内容。检索摘要，如果通过PubMed Central（PMC）可用，还包括全文片段。首先使用ADA_list_standards_sections获取各章节... | 可用 | 默认分类 |
| Anaconda_get_package | Anaconda_get_package | 从Anaconda.org特定频道获取conda包的详细信息。返回包的完整元数据，包括描述、所有版本、平台可用性、下载量、主页URL、许可证和所有者详情。使用格式'{channel}/{package... | 可用 | 默认分类 |
| ArtIC_get_artwork | ArtIC_get_artwork | 通过数字ID从芝加哥艺术学院收藏中获取特定艺术品的详细信息。返回完整元数据，包括标题、艺术家、日期、媒介、尺寸、来源、展览历史和IIIF图像URL。无需认证。使用ArtIC_search_artwor... | 可用 | 默认分类 |
| CORE_get_fulltext_snippets | CORE_get_fulltext_snippets | 获取开放获取PDF(通常由CORE_search_papers返回)并返回围绕提供术语的有界文本片段。当基于索引的搜索错过仅正文关键词时，这是本地(下载+扫描)全文搜索的后备方案。提取后端:PyMuP... | 可用 | 默认分类 |
| CRAN_get_package_versions | CRAN_get_package_versions | 从CRAN获取R包的所有历史版本及其发布日期和依赖项。适用于理解包演化、检查兼容性和查找特定功能添加时间。返回完整的版本时间线及发布日期。 | 可用 | 默认分类 |
| EPMC_get_citations | EPMC_get_citations | 从Europe PMC获取引用特定论文的文章。给定PubMed ID（PMID），返回引用文章的列表，包括标题、作者、期刊、出版年份和引用次数。用于追踪研究影响、识别后续研究和发现相关工作。对系统综述... | 可用 | 默认分类 |
| EPMC_get_references | EPMC_get_references | 从Europe PMC获取特定论文的参考文献列表（书目）。给定PubMed ID（PMID），返回该论文引用的所有文章（其参考文献列表）。这是引用的反向操作：不是查找谁引用了论文，而是查找论文引用了哪... | 可用 | 默认分类 |
| Finish | Finish | 标记多步推理的结束。 | 可用 | 默认分类 |
| IDR_get_study | IDR_get_study | 通过项目ID获取图像数据资源（IDR）中特定成像研究（项目）的详细信息。返回研究元数据，包括名称、描述、数据集数量和关联图像数据的链接。使用IDR_list_studies查找研究ID。 | 可用 | 默认分类 |
| OpenCitations_get_citation_count | OpenCitations_get_citation_count | 通过OpenCitations COCI索引获取科学文章的总被引次数。返回论文在OpenCitations数据库中的被引频次。当仅需计数时比获取完整引用列表更高效。 | 可用 | 默认分类 |
| OpenCitations_get_citations | OpenCitations_get_citations | 通过OpenCitations COCI索引获取引用指定科学文章的论文列表（被引次数及引用文献）。返回该论文发表后被哪些文献引用。适用于衡量研究影响力、追踪后续研究及分析论文对后续研究的影响。 | 可用 | 默认分类 |
| OpenCitations_get_references | OpenCitations_get_references | 通过OpenCitations COCI索引获取指定科学文章的参考文献列表。OpenCitations是一个基于CrossRef的免费开放学术引文数据库。返回包含DOI、发表日期及文献间时间跨度的引文... | 可用 | 默认分类 |
| OpenFoodFacts_get_product | OpenFoodFacts_get_product | 通过条形码使用Open Food Facts数据库获取特定食品的详细信息。返回完整的营养数据、成分、过敏原、Nutri-Score、生态评分和产品图片。无需认证。 | 可用 | 默认分类 |
| OutputSummarizationComposer | OutputSummarizationComposer | 通过分块长输出、使用AI摘要处理每个块并合并结果来组合输出摘要工作流 | 可用 | 默认分类 |
| PyPIPackageInspector | PyPIPackageInspector | 从PyPI和GitHub提取全面的软件包信息进行质量评估。提供流行度（下载量、星标、分支）、维护情况（发布频率、近期活动）、文档质量、Python版本兼容性和安全指标等详细指标，返回0-100分的综合... | 可用 | 默认分类 |
| SemanticScholar_get_author | SemanticScholar_get_author | 通过作者ID获取Semantic Scholar上特定作者的详细资料。返回姓名、h指数、引用次数、论文数量、所属机构、主页及可选的论文列表（含标题、年份和引用次数）。需先使用SemanticSchol... | 可用 | 默认分类 |
| SemanticScholar_get_paper | SemanticScholar_get_paper | 通过论文ID、DOI、PubMed ID或其他标识符从Semantic Scholar获取特定论文的详细元数据。返回标题、摘要、作者、引用次数、参考文献数量、期刊、出版物类型、开放获取PDF链接及外部... | 可用 | 默认分类 |
| SemanticScholar_get_recommendations | SemanticScholar_get_recommendations | 获取Semantic Scholar针对给定论文的推荐论文。基于Semantic Scholar的推荐算法返回与输入论文相似或相关的论文。适用于文献发现——查找可能遗漏的相关工作。需要Semantic... | 可用 | 默认分类 |
| SoilGrids_get_properties | SoilGrids_get_properties | 通过ISRIC SoilGrids API获取地球任意位置的土壤属性。返回包括pH值、有机碳(SOC)、粘土/砂/粉砂含量、容重、阳离子交换容量等多层土壤深度（0-5cm至100-200cm）的定量数... | 可用 | 默认分类 |
| Survival_log_rank_test | Survival_log_rank_test | 执行Mantel-Cox对数秩检验比较两组生存率。检验生存曲线相同的零假设。返回卡方统计量、p值、每组的观察与预期事件数。p值<0.05表示生存率存在统计学显著差异。适用于：比较治疗组、高表达与低表达... | 可用 | 默认分类 |
| SwissDock_retrieve_results | SwissDock_retrieve_results | 获取已完成的SwissDock对接任务结果。返回对接输出文件的下载链接及元数据。结果归档(tar.gz)包含：预测结合构象(PDB文件)、对接分数（能量与排名）、聚类信息和可视化文件。仅在check_... | 需要登录 | 默认分类 |
| TCIA_get_body_part_values | TCIA_get_body_part_values | 获取TCIA影像集合中检查的身体部位。返回用于筛选系列查询的身体部位名称。可选按集合或模态筛选。 | 可用 | 默认分类 |
| TCIA_get_modality_values | TCIA_get_modality_values | 获取特定TCIA集合或所有集合中可用的影像模态。返回模态代码，如CT、MR、PT（PET）、CR、DX、US（超声）、NM。 | 可用 | 默认分类 |
| TCIA_get_series_metadata | TCIA_get_series_metadata | 通过Series Instance UID获取TCIA中特定影像系列的详细DICOM元数据。返回设备信息、采集参数和系列属性。 | 可用 | 默认分类 |
| ToolDescriptionOptimizer | ToolDescriptionOptimizer | 通过生成测试用例、执行测试、分析结果并建议改进工具及其参数的描述，优化工具描述和参数描述。可选择将完整的优化报告保存到文件而不覆盖原始文件。 | 可用 | 默认分类 |
| ToolDiscover | ToolDiscover | 基于简短描述生成符合ToolUniverse规范的工具，采用XML格式同步生成代码和规范。自动发现相似工具，筛选高质量参考信息，并通过代理优化迭代优化工具。 | 可用 | 默认分类 |
| Tool_Finder | Tool_Finder | 根据提供的描述从工具箱中检索相关工具，功能更强大的高级版本。 | 可用 | 默认分类 |
| Tool_Finder_Keyword | Tool_Finder_Keyword | 基于关键字的简单工具查找器，用于通过文本匹配发现相关工具 | 可用 | 默认分类 |
| Tool_Finder_LLM | Tool_Finder_LLM | 基于LLM的工具查找器，使用自然语言处理智能选择与用户查询相关的工具。该工具分析所有可用工具描述，并使用LLM确定哪些工具对给定任务或问题最有帮助。 | 可用 | 默认分类 |
| Tool_RAG | Tool_RAG | 根据提供的描述从工具箱中检索相关工具 | 可用 | 默认分类 |
| USCensus_get_population | USCensus_get_population | 从美国人口普查局API获取人口和人口统计数据。可访问十年一次的人口普查和美国社区调查（ACS）数据，涵盖国家、州、县和城市级别。基本使用无需认证密钥。变量包括总人口、住房单位、年龄组和种族/民族细分。... | 可用 | 默认分类 |
| WFGY_triage_llm_rag_failure | WFGY_triage_llm_rag_failure | 生成结构化提示包(系统+用户消息)以使用WFGY问题映射(No.1..No.16)对LLM/RAG故障进行分类。返回提示、最小修复检查表和公共问题映射链接。不调用LLM或外部API。 | 可用 | 默认分类 |
| WorldBank_get_country | WorldBank_get_country | 从世界银行数据库获取国家元数据。返回国家名称、ISO代码、世界区域、收入水平、贷款类型、首都及地理坐标。在查询世界银行指标前查找国家代码时必备。 | 可用 | 默认分类 |
| dbfetch_fetch_batch | dbfetch_fetch_batch | 批量获取多个数据库条目。支持逗号分隔的ID或ID列表。返回指定格式的条目。 | 可用 | 默认分类 |
| dbfetch_fetch_entry | dbfetch_fetch_entry | 从各种数据库（UniProt、PDB等）按ID获取单个数据库条目，支持FASTA、XML、JSON和其他格式。 | 可用 | 默认分类 |
| dbfetch_list_databases | dbfetch_list_databases | 列出Dbfetch服务中所有可用的数据库。注意：由于API端点仅限网页使用，此处返回的是常见数据库名称的静态列表。 | 可用 | 默认分类 |
| dbfetch_list_formats | dbfetch_list_formats | 列出特定数据库可用的输出格式。注意：由于API端点仅限网页使用，此处返回的是常见格式名称的静态列表。 | 可用 | 默认分类 |
| dynamic_package_discovery | dynamic_package_discovery | 动态搜索PyPI并根据需求评估软件包 | 可用 | 默认分类 |
| embedding_database_add | embedding_database_add | 向现有按集合存储的数据仓库（<name>.db + <name>.faiss）追加文档。使用相同的L2归一化余弦设置。强制要求模型/维度与集合一致。 | 可用 | 默认分类 |
| embedding_database_create | embedding_database_create | 创建按集合存储的数据仓库：<name>.db（SQLite）+ <name>.faiss（FAISS）。使用选定的提供程序（openai/azure/huggingface/local）嵌入文档。向量... | 可用 | 默认分类 |
| ena_get_entry | ena_get_entry | 通过登录号从ENA获取条目信息。仅支持EMBL/GenBank登录号(如U00096, AJ312385, M15390)。不支持RefSeq登录号(NC_*, NM_*, NP_*前缀)。当前从FA... | 可用 | 默认分类 |
| ena_get_entry_history | ena_get_entry_history | 通过登录号获取ENA条目的版本历史。仅支持EMBL/GenBank登录号(如U00096, AJ312385, M15390)。不支持RefSeq登录号(NC_*, NM_*, NP_*前缀)。返回条... | 可用 | 默认分类 |
| ena_get_entry_summary | ena_get_entry_summary | 通过登录号获取ENA条目的完整摘要信息。仅支持EMBL/GenBank登录号(如U00096, AJ312385, M15390)。不支持RefSeq登录号(NC_*, NM_*, NP_*前缀)。返... | 可用 | 默认分类 |
| get_assembly_summary | get_assembly_summary | 获取与PDB条目关联的组装关键组成及对称性摘要。 | 可用 | 默认分类 |
| get_ec_number_by_entity_id | get_ec_number_by_entity_id | 获取实体的酶学委员会(EC)编号。 | 可用 | 默认分类 |
| get_em_3d_fitting_and_reconstruction_details | get_em_3d_fitting_and_reconstruction_details | 获取PDB条目对应的EM 3D拟合模型详情及关联的3D重建信息。 | 可用 | 默认分类 |
| get_oligosaccharide_descriptors_by_entity_id | get_oligosaccharide_descriptors_by_entity_id | 获取PDB条目中分支实体（如寡糖）的结构描述符。 | 可用 | 默认分类 |
| grep_tools | grep_tools | 使用简单文本匹配或正则表达式模式搜索工具。支持简单文本搜索（默认，代理友好）和正则表达式模式（高级）。独立于Tool_Finder_Keyword，使用基本文本/正则匹配，无需TF-IDF或NLP处理... | 可用 | 默认分类 |
| intact_get_interaction_details | intact_get_interaction_details | 通过IntAct相互作用ID获取特定相互作用的详细信息。需要'EBI-XXXXXX-EBI-YYYYYY'格式的ID。可通过intact_get_interactions或intact_search_... | 可用 | 默认分类 |
| list_tools | list_tools | 列出具有多种输出模式的工具。默认模式为'names'用于快速扫描。推荐工作流程：从默认或模式'categories'开始以获取概览，然后使用'get_tool_info'工具获取特定工具的描述/详细信... | 可用 | 默认分类 |
| python_code_executor | python_code_executor | 在具有超时和资源限制的沙盒环境中安全执行Python代码片段。支持变量传递和结果提取。 | 可用 | 默认分类 |
| scite_get_tallies | scite_get_tallies | 使用scite.ai获取科学论文的智能引用统计。scite通过分析引用上下文将引用分类为支持、反驳或提及。返回支持引用（确认论文主张）、反驳引用（质疑主张）、提及引用（中性引用）和总引用文献的数量。支... | 可用 | 默认分类 |

#### 学术文献与引用 (7个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| Crossref_get_work | Crossref_get_work | 通过DOI（数字对象标识符）获取特定学术作品的完整元数据。返回全面的书目信息，包括标题、摘要、带有隶属关系和ORCID的完整作者列表、期刊详情、出版日期、卷/期/页码、参考文献、引用、许可证、资助信息... | 可用 | 匹配学术文献关键词 |
| DataCite_get_doi | DataCite_get_doi | 通过DOI从DataCite获取研究数据集或出版物的元数据。DataCite是研究数据DOI的主要注册机构，涵盖存储在Zenodo、Dryad、Figshare等数千个机构存储库中的数据集、软件、样本... | 可用 | 匹配学术文献关键词 |
| get_arxiv_info | get_arxiv_info | 获取arxiv的全面信息——arXiv预印本库访问工具 | 可用 | 匹配学术文献关键词 |
| openalex_get_author | openalex_get_author | 通过作者ID（A...）获取单个OpenAlex作者。您可以传递短ID（例如"A5001226970"）或完整URL（例如"https://openalex.org/A5001226970"）。 | 可用 | 匹配学术文献关键词 |
| openalex_get_institution | openalex_get_institution | 通过机构ID（I...）获取单个OpenAlex机构。您可以传递短ID（例如"I136199984"）或完整URL（例如"https://openalex.org/I136199984"）。 | 可用 | 匹配学术文献关键词 |
| openalex_get_work | openalex_get_work | 通过OpenAlex作品ID（W...）获取单个OpenAlex作品（论文）。您可以传递短ID（例如"W2626778328"）或完整URL（例如"https://openalex.org/W2626... | 可用 | 匹配学术文献关键词 |
| openalex_get_work_by_doi | openalex_get_work_by_doi | 通过DOI获取单个OpenAlex作品（论文）。提供类似"10.65215/2q58a426"的DOI字符串（也可以传递类似"https://doi.org/10.65215/2q58a426"的DO... | 可用 | 匹配学术文献关键词 |

#### 网页与搜索 (6个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| GitHub_get_repository | GitHub_get_repository | 获取特定GitHub公共仓库的详细元数据。返回完整的仓库信息，包括描述、统计（星标、分叉、关注者、未解决问题）、编程语言、主题、许可证、README存在性和最近活动。使用owner/repo格式的fu... | 可用 | 匹配网页搜索关键词 |
| Wikipedia_get_content | Wikipedia_get_content | 从维基百科文章中提取内容。可提取引言、摘要或全文内容。无需API密钥。 | 可用 | 匹配网页搜索关键词 |
| Wikipedia_get_featured_content | Wikipedia_get_featured_content | 使用Wikipedia REST API获取特定日期的特色内容，包括当日特色文章、最受欢迎文章、当日图片和历史事件。无需认证。适用于每日简报和趋势内容发现。 | 可用 | 匹配网页搜索关键词 |
| Wikipedia_get_summary | Wikipedia_get_summary | 获取维基百科文章的简要摘要/引言。这是一个便捷工具，仅提取文章的第一段(落)。无需API密钥。 | 可用 | 匹配网页搜索关键词 |
| get_webpage_text_from_url | get_webpage_text_from_url | 将URL渲染为PDF并提取其文本（支持JavaScript）。 | 可用 | 匹配网页搜索关键词 |
| get_webpage_title | get_webpage_title | 获取网页并返回其<title>标签的内容。 | 可用 | 匹配网页搜索关键词 |

#### 文件与执行 (6个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| GitHub_get_user_profile | GitHub_get_user_profile | 通过用户名获取公共GitHub用户资料。返回用户元数据，包括姓名、简介、公司、位置、公共仓库和代码片段数量、关注者/关注数量以及账户创建日期。无需API密钥（未认证状态下每小时限60次请求）。适用于查... | 可用 | 匹配文件执行关键词 |
| download_binary_file | download_binary_file | 下载二进制文件（如图像、视频、可执行文件），采用分块流式传输以优化内存管理。特别适合大文件下载。 | 可用 | 匹配文件执行关键词 |
| download_file | download_file | 从HTTP/HTTPS URL下载文件，支持跨平台（Windows、Mac、Linux）。类似于curl但独立于平台。可以保存到指定路径或临时目录。 | 可用 | 匹配文件执行关键词 |
| download_text_content | download_text_content | 从URL下载并返回文本内容。针对文本文件优化，支持自动编码检测。 | 可用 | 匹配文件执行关键词 |
| execute_tool | execute_tool | 直接使用自定义参数执行ToolUniverse工具。这是在ToolUniverse系统中运行任何工具的主要方式。您必须先获取工具定义以确定要传递的参数。 | 可用 | 匹配文件执行关键词 |
| python_script_runner | python_script_runner | 在具有资源限制和超时的隔离子进程中运行Python脚本文件。支持命令行参数和环境变量。 | 可用 | 匹配文件执行关键词 |

#### 统计分析 (5个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| InterProScan_get_job_status | InterProScan_get_job_status | 检查InterProScan分析作业状态。当scan_sequence在完成前返回时使用。状态：运行中、已完成、失败、错误、未找到。 | 可用 | 匹配统计分析关键词 |
| MGnify_list_analyses | MGnify_list_analyses | 列出与研究编号关联的分析（分类/功能输出）。用于枚举可用的处理结果以便程序化检索。 | 可用 | 匹配统计分析关键词 |
| SwissDock_check_job_status | SwissDock_check_job_status | 通过会话ID检查SwissDock对接任务状态。返回当前状态：RUNNING（进行中需轮询）、FINISHED（可获取结果）、ERROR（失败）或NOT_FOUND（无效会话）。用于监控已提交的长时间... | 需要登录 | 匹配统计分析关键词 |
| Unpaywall_check_oa_status | Unpaywall_check_oa_status | 通过DOI查询Unpaywall检查开放获取状态和OA位置。需要提供联系邮箱以访问API。 | 需要API密钥 | 匹配统计分析关键词 |
| get_core_refinement_statistics | get_core_refinement_statistics | 检索给定PDB结构的核心精修统计信息，包括R因子、占有率、相位误差和溶剂模型参数。 | 可用 | 匹配统计分析关键词 |

#### 文档处理 (4个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| SemanticScholar_get_pdf_snippets | SemanticScholar_get_pdf_snippets | 从Semantic Scholar获取开放获取的PDF，并返回围绕提供术语的有界文本片段。使用markitdown将PDF转换为markdown。当关键细节（方法、实验参数）在全文而非摘要中时非常有用... | 可用 | 匹配文档处理关键词 |
| convert_to_markdown | convert_to_markdown | 将http:、https:、file:或data: URI描述的资源转换为markdown格式。 | 可用 | 匹配文档处理关键词 |
| ena_get_sequence_xml | ena_get_sequence_xml | 从ENA获取研究、样本、运行、实验、分析或分类记录的XML格式元数据。序列记录不支持XML格式 - 序列登录号请使用ena_get_sequence_fasta或ena_get_sequence_em... | 可用 | 匹配文档处理关键词 |
| get_pypdf2_info | get_pypdf2_info | 获取关于PyPDF2的全面信息——PDF操作库 | 可用 | 匹配文档处理关键词 |

#### 数据存储与检索 (3个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| Dataverse_get_dataset | Dataverse_get_dataset | 通过持久DOI标识符获取特定哈佛Dataverse数据集的详细元数据。返回全面信息，包括数据集ID、版本详情、引用元数据（标题、作者、描述、主题、关键词）、使用条款和发布日期。持久ID是搜索结果中的D... | 可用 | 匹配数据存储关键词 |
| HuggingFace_get_model | HuggingFace_get_model | 通过作者和模型名称获取HuggingFace Hub上特定模型的详细元数据。返回包括模型架构、标签、下载/点赞数、创建日期、许可证、交互测试组件数据和卡片元数据等综合信息。HuggingFace上的模... | 可用 | 匹配数据存储关键词 |
| OpenML_get_dataset | OpenML_get_dataset | 通过数字ID获取OpenML特定数据集的详细元数据。返回包括描述、数据格式、创建者、收集日期、许可证、下载链接（ARFF和Parquet格式）、默认目标属性、标签、引用信息和版本历史在内的全面信息。知... | 可用 | 匹配数据存储关键词 |

#### 知识图谱与本体 (2个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| Wikidata_SPARQL_query | Wikidata_SPARQL_query | 在Wikidata上执行SPARQL查询以获取结构化数据。该工具支持Scholia风格的可视化，可查询学术主题、作者、机构和研究关系。 | 可用 | 匹配知识图谱关键词 |
| Wikidata_get_entity | Wikidata_get_entity | 通过Q编号获取一个或多个Wikidata实体的详细结构化数据。返回标签、描述、别名、站点链接及声明（陈述）。建议先使用Wikidata_search_entities查找实体ID。无需编写SPARQL... | 可用 | 匹配知识图谱关键词 |

#### 机器学习 (1个工具)

| 工具名 | 中文名称 | 描述 | 可用性 | 分类原因 |
|--------|----------|------|--------|----------|
| ModelDB_get_paper | ModelDB_get_paper | 通过论文ID获取ModelDB中引用的科学论文详情。返回论文标题、完整引用名称、参考文献及关联模型。ModelDB中的论文链接到计算神经科学模型，代表描述这些模型的出版物。使用ModelDB_get_... | 可用 | 匹配机器学习关键词 |

## 3. 典型应用场景

### 3.1 材料科学研究

- 晶体结构查询与分析 (COD)
- 材料机器学习描述符 (DScribe)
- 分子深度学习 (SchNetPack, PyTorch Geometric)
- 药物发现与材料科学AI (DeepChem)

### 3.2 化学研究

- 化合物数据库检索 (PubChem, ChEMBL, ChEBI)
- 分子结构与性质计算
- 化学反应与合成路线设计
- 光谱数据分析

### 3.3 通用科研工具

- 学术文献检索与引用分析
- 研究数据存储与共享
- 文档处理与格式转换
- Python科学计算包信息

## 4. 使用建议

### 4.1 可用性说明

- **可用**: 可直接使用，无需额外配置
- **需要API密钥**: 需要申请API密钥才能使用
- **需要登录**: 需要注册账号并登录才能使用
- **需要订阅**: 需要付费订阅才能使用
- **需要安装依赖**: 需要安装Python包才能使用

### 4.2 推荐工具

#### 材料科学

- **COD_search_structures**: 晶体结构数据库搜索
- **get_deepchem_info**: 材料科学AI工具包
- **get_dscribe_info**: 材料机器学习描述符库

#### 化学

- **ChEMBL_search_activities**: ChEMBL生物活性数据
- **PubChem_search_compounds**: PubChem化合物搜索
- **ChEBI_search_entities**: ChEBI化学实体搜索

#### 通用工具

- **arxiv_search_papers**: arXiv论文搜索
- **SemanticScholar_search_papers**: Semantic Scholar论文搜索
- **python_code_executor**: Python代码执行
