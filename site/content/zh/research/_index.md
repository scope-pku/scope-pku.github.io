---
title: 研究
translationKey: research
---

本课题组主要开展软凝聚态物理与计算物理研究，关注纳米尺度下物质的行为，并运用先进的计算工具与方法开展研究。主要研究方向包括：

{{< research-story title="复杂物质中的相变与临界现象" image="/media/research-01.png" width="1600" height="1200" alt="展示两种液体结构的模拟快照" caption="课题组液-液相变研究的示意图。" >}}

气、液、固之间的相变可由统计物理、热力学和凝聚态物理描述\[1\]。对于存在液态多形性的复杂物质，这类描述更为困难。水、硅、硫、磷、镓和氢虽具有不同的电子与分子结构，却在液态表现出相似的结构、动力学和热力学反常\[2-6\]。

在液-液临界点图景中，单组分物质可能存在低密度液体（LDL）、高密度液体（HDL）以及二者之间的液-液相变（LLPT）。液-液临界点（LLCP）及其临界涨落可能与复杂液体的反常性质有关。

由于 LLCP 通常深藏于结晶迅速发生的深过冷区，实验验证仍然十分困难。如何通过更易达到的条件追踪 LLPT 与 LLCP 的行为，是这一领域尚待解决的核心问题。

{{< /research-story >}}

### 参考文献：

1. [X. Yu, R. Huang, H. Song, L. Xu, et al. Phys. Rev. Lett. 129, 210601 (2021)](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.129.210601)
2. [R. Li, G. Sun, L. Xu, et al. The Journal of Chemical Physics, 145, 054506 (2016)](https://pubs.aip.org/aip/jcp/article/145/5/054506/316547/Anomalous-properties-and-the-liquid-liquid-phase)
3. [Z. Sun, D. Pan, L. Xu\*, and E. G. Wang\*, Proc. Natl. Acad. Sci. USA 109, 13177-13181 (2012)](https://www.pnas.org/doi/10.1073/pnas.1206879109)
4. [L. Xu\*, P. Kumar, S. V. Buldyrev, S.-H. Chen, P. H. Poole, et al. Proc. Natl. Acad. Sci. USA 102, 16558 (2005)](https://www.pnas.org/doi/10.1073/pnas.0507870102)
5. [L. Xu\*, S. V. Buldyrev, F. W. Starr, F. Mallamace, and H. E. Stanley. Nature Physics 5, 565-569 (2009).](https://www.nature.com/articles/nphys1328)
6. [J. Luo, L. Xu\*, E. Lascaris, H. E. Stanley, and S. V. Buldyrev, Phys. Rev. Lett. 112, 135701 (2014).](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.112.135701)

{{< research-story title="界面水的结构与动力学" image="/media/research-02.jpg" width="1395" height="1400" alt="界面水分子的原子力显微镜成像与模拟" caption="采用类四极针尖对界面水进行的原子力显微镜成像与模拟。" >}}

界面水与物理、化学、生物、能源和材料科学等多个领域密切相关。界面离子水合物也广泛存在于电催化、海水淡化、生物离子通道和化学反应等过程。理解不同界面氢键网络（无论是否含离子）的原子尺度结构，是解释水-固界面性质的重要基础。

基于实验数据，结合密度泛函理论计算和原子力显微镜（AFM）图像模拟，我们研究不同基底上的氢键网络\[2-8\]，并考察其动力学性质、质子转移机制以及冰表面与预熔行为\[1\]。

逐次尝试并比对模拟与实验 AFM 图像往往较为耗时，因此我们也研究如何借助机器学习提高结构解析效率\[9\]。我们开发了 [AmorAFM](https://github.com/seasonlo/AmorAFM)，利用机器学习从 AFM 图像中解析非晶冰层（AIL）的原子结构。

{{< /research-story >}}

### 参考文献：

1. [J. Hong, Y. Tian, T. Liang, et al. Nature (2024)](https://www.nature.com/articles/s41586-024-07427-8)
2. [D. Wu, Z. Zhao, B. Lin, Y. Song, et al. Science 384, 1254-1259 (2024)](https://www.science.org/doi/10.1126/science.ado1544)
3. [Y. Tian, Y. Song, Y. Xia, J. Hong, Y. Huang, et al. Nature Nanotechnology 10, 1038. (2024).](https://www.nature.com/articles/s41565-023-01550-9)
4. [Y. Tian, B. Huang, Y. Song, et al. Nature Communications 15, 738. (2024).](https://www.nature.com/articles/s41467-024-52131-w)
5. [Y. Tian\*, J. Hong\*, D. Cao\*, S. You\*, Y. Song, et al. Science 377, 315-319 (2022).](https://www.science.org/doi/10.1126/science.abo0823)
6. [D. Cao, Y. Song, J. Peng, et al. Front Chem. 9, 745446 (2021)](https://www.frontiersin.org/articles/10.3389/fchem.2021.745446/full)
7. [D. Cao, Y. Song, J. Peng, et al. Front Chem. 7, 626 (2019)](https://www.frontiersin.org/articles/10.3389/fchem.2019.00626/full)
8. [J. Peng, D. Cao, Z. He, et al. Nature 557, 701-705 (2018).](https://www.nature.com/articles/s41586-018-0122-2)
9. [B. Tang\*, Y. Song\*, M. Qin\*, et al. National Science Review. nwac282 (2022).](https://academic.oup.com/nsr/article/10/7/nwac282/6901515?login=true)

{{< research-story title="非晶固体与非平衡相变" image="/media/research-03.png" width="976" height="472" alt="受限液体结晶过程的三个模拟快照" caption="模拟中受限液体在三个连续时刻的演化。" image2="/media/research-04.png" width2="1381" height2="1400" alt2="二维模型玻璃中的本征矢量场" caption2="二维模型玻璃中振动激发的本征矢量场。" >}}

近四十年前，研究者在水中发现了类似一级相变的非平衡玻璃-玻璃转变（GGT），并识别出两种非晶冰。此后，人们又在类水复杂物质\[1,2\]、胶体、颗粒物质、聚合物和液晶等体系中观察到 GGT。由于缺少成熟理论，描述玻璃转变和玻璃-玻璃转变等非平衡相变仍然十分困难。

我们的一个研究方向是深过冷区中的受限液体。在生物学、地质学等领域，材料性质往往强烈依赖其中水的含量与行为\[3\]。纳米限域下的结晶对科学研究和工程应用同样重要，但其机制仍未得到充分理解。我们利用分子动力学模拟研究具有各向同性成对相互作用和类水性质的受限液体。结果表明，增强液体与表面的相互作用有利于液体在无结构表面结晶，却倾向于抑制其在非晶表面结晶\[4\]。

我们也研究非晶固体的行为。玻璃十分常见，但其若干共性背后的基础物理仍未得到充分理解。非晶材料在较小外加应变下呈弹性响应，而在中等程度形变下会发生难以表征和预测的不可逆结构重排。

近年来，研究者尝试寻找无序固体失效的结构预测量，以识别塑性形变的先兆。我们研究二维模型玻璃中与振动激发相关的本征矢量场的拓扑特征，并将形变前的玻璃结构与随后的塑性事件联系起来\[5\]。

{{< /research-story >}}

### 参考文献：

1. [G. Sun, L. Xu, N. Giovambattista. Phys. Rev. Lett. 120, 035701 (2018)](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.120.035701)
2. [Y. Liu, G. Sun, L. Xu. The Journal of Chemical Physics, 154, 134503 (2021)](https://pubs.aip.org/aip/jcp/article/154/13/134503/1065570/Glass-polyamorphism-in-gallium-Two-amorphous-solid)
3. [S. Cerveny, F. Mallamace, J. Swenson, M. Vogel, and L. Xu. Chemical Reviews (2015)](https://pubs.acs.org/doi/full/10.1021/acs.chemrev.5b00609)
4. [G. Sun, N. Giovambattista, E. G. Wang, and L. Xu\*, et al. Soft Matter 9, 11374 (2013)](https://pubs.rsc.org/en/content/articlelanding/2013/sm/c3sm52206g)
5. [Z. Wu, Y. Chen, W. Wang, W. Kob, L. Xu, Nat. Commun. 14, 2955 (2023)](https://www.nature.com/articles/s41467-023-38547-w)
