---
title: "Research"
translationKey: research
aliases:
  - "/Research.htm"
---
We are a computational research group in soft condensed matter physics and computational physics. Our group focuses on investigating the behavior of matter at the nanoscale, utilizing state-of-the-art computational tools and techniques. Our research includes:

## Phase transition and critical phenomena in complex substances

Phase transitions between gas, liquid, and solid states can be described by statistical physics, thermodynamics, and condensed matter physics\[1\]. These descriptions become more difficult for complex substances with liquid polymorphisms. Water, silicon, sulfur, phosphorus, gallium, and hydrogen have distinct electronic and molecular structures, yet exhibit related structural, dynamic, and thermodynamic anomalies in their liquid states\[2-6\].

In the liquid-liquid critical point scenario, a single-component substance may exhibit a low-density liquid (LDL), a high-density liquid (HDL), and a transition between them (LLPT). The liquid-liquid critical point (LLCP) and its critical fluctuations may contribute to the anomalous properties of complex liquids.

Experimental verification remains challenging because LLCPs are usually buried in the deeply supercooled region, where crystallization occurs rapidly. A central open question is how LLPT and LLCP behavior can be traced through more readily accessible conditions.

{{< figure src="/media/research-01.png" alt="Simulation snapshot illustrating two liquid structures" caption="Illustration accompanying the group's work on liquid-liquid phase transitions." >}}

### References:

1. [X. Yu, R. Huang, H. Song, L. Xu, et al. Phys. Rev. Lett. 129, 210601 (2021)](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.129.210601)
2. [R. Li, G. Sun, L. Xu, et al. The Journal of Chemical Physics, 145, 054506 (2016)](https://pubs.aip.org/aip/jcp/article/145/5/054506/316547/Anomalous-properties-and-the-liquid-liquid-phase)
3. [Z. Sun, D. Pan, L. Xu\*, and E. G. Wang\*, Proc. Natl. Acad. Sci. USA 109, 13177-13181 (2012)](https://www.pnas.org/doi/10.1073/pnas.1206879109)
4. [L. Xu\*, P. Kumar, S. V. Buldyrev, S.-H. Chen, P. H. Poole, et al. Proc. Natl. Acad. Sci. USA 102, 16558 (2005)](https://www.pnas.org/doi/10.1073/pnas.0507870102)
5. [L. Xu\*, S. V. Buldyrev, F. W. Starr, F. Mallamace, and H. E. Stanley. Nature Physics 5, 565-569 (2009).](https://www.nature.com/articles/nphys1328)
6. [J. Luo, L. Xu\*, E. Lascaris, H. E. Stanley, and S. V. Buldyrev, Phys. Rev. Lett. 112, 135701 (2014).](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.112.135701)

## Interfacial water structure and dynamics

Interfacial water is relevant across physics, chemistry, biology, energy, and materials science. Interfacial ionic hydrates also arise in electrocatalysis, seawater desalination, biological ion channels, and chemical reactions. Understanding their atomic-scale hydrogen-bond networks is important for explaining the properties of water-solid interfaces.

Using density functional theory calculations and AFM image simulations based on experimental data, we investigate hydrogen-bond networks on different substrates\[2-8\]. We study their dynamics, proton-transfer mechanisms, ice surfaces, and premelting behavior\[1\].

Because matching simulated and experimental AFM images by trial and error can be time-consuming, we also investigate machine-learning-assisted structure determination\[9\]. We developed [AmorAFM](https://github.com/seasonlo/AmorAFM) to resolve the atomic structure of the amorphous ice layer (AIL) from AFM images using machine learning.

{{< figure src="/media/research-02.jpg" alt="AFM imaging and simulation of an interfacial water molecule" caption="AFM imaging and simulation of interfacial water with a quadrupole-like tip." >}}

### References:

1. [J. Hong, Y. Tian, T. Liang, et al. Nature (2024)](https://www.nature.com/articles/s41586-024-07427-8)
2. [D. Wu, Z. Zhao, B. Lin, Y. Song, et al. Science 384, 1254-1259 (2024)](https://www.science.org/doi/10.1126/science.ado1544)
3. [Y. Tian, Y. Song, Y. Xia, J. Hong, Y. Huang, et al. Nature Nanotechnology 10, 1038. (2024).](https://www.nature.com/articles/s41565-023-01550-9)
4. [Y. Tian, B. Huang, Y. Song, et al. Nature Communications 15, 738. (2024).](https://www.nature.com/articles/s41467-024-52131-w)
5. [Y. Tian\*, J. Hong\*, D. Cao\*, S. You\*, Y. Song, et al. Science 377, 315-319 (2022).](https://www.science.org/doi/10.1126/science.abo0823)
6. [D. Cao, Y. Song, J. Peng, et al. Front Chem. 9, 745446 (2021)](https://www.frontiersin.org/articles/10.3389/fchem.2021.745446/full)
7. [D. Cao, Y. Song, J. Peng, et al. Front Chem. 7, 626 (2019)](https://www.frontiersin.org/articles/10.3389/fchem.2019.00626/full)
8. [J. Peng, D. Cao, Z. He, et al. Nature 557, 701-705 (2018).](https://www.nature.com/articles/s41586-018-0122-2)
9. [B. Tang\*, Y. Song\*, M. Qin\*, et al. National Science Review. nwac282 (2022).](https://academic.oup.com/nsr/article/10/7/nwac282/6901515?login=true)

## Amorphous solids and non-equilibrium phase transitions

Almost four decades ago, a first-order-like non-equilibrium glass-glass transition (GGT) was discovered in water, in which two forms of amorphous ice were identified. GGT was subsequently observed in other systems, including water-like complex substances\[1,2\], colloids, particulate matter, polymers, and liquid crystals. Describing non-equilibrium phase transitions such as glass transition and glass-glass transition remains challenging because well-established theories are lacking.

{{< figure src="/media/research-03.png" alt="Three simulation snapshots of confined liquid crystallization" caption="Evolution of a confined liquid in simulation at three successive times." >}}

One direction is the study of confined liquids in the supercooled region. Such liquids are relevant in biology, geology, and other settings where material properties depend strongly on the amount and behavior of water\[3\]. Crystallization under nanoscale confinement is also important in scientific and engineering applications, but remains poorly understood. Using molecular dynamics simulations, we study a confined liquid with isotropic pair interactions and water-like properties. Increasing the liquid-surface interaction strength favors crystallization at structureless surfaces, but tends to suppress crystallization at amorphous surfaces\[4\].

{{< figure src="/media/research-04.png" alt="Eigenvector field in a two-dimensional model glass" caption="Eigenvector field of vibrational excitations in a two-dimensional model glass." >}}

We also study the behavior of amorphous solids. Glasses are commonplace, but the fundamental physics underlying several of their shared features is not yet well understood. They respond elastically to small applied strain, then undergo irreversible structural rearrangements at moderate deformation that are difficult to characterize and predict.

Recent work has sought structural predictors for the failure of disordered solids by identifying precursors to plastic deformation. We investigate the topology of the eigenvector field associated with vibrational excitations in two-dimensional model glasses, linking the structure before deformation to subsequent plastic events\[5\].

### References:

1. [G. Sun, L. Xu, N. Giovambattista. Phys. Rev. Lett. 120, 035701 (2018)](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.120.035701)
2. [Y. Liu, G. Sun, L. Xu. The Journal of Chemical Physics, 154, 134503 (2021)](https://pubs.aip.org/aip/jcp/article/154/13/134503/1065570/Glass-polyamorphism-in-gallium-Two-amorphous-solid)
3. [S. Cerveny, F. Mallamace, J. Swenson, M. Vogel, and L. Xu. Chemical Reviews (2015)](https://pubs.acs.org/doi/full/10.1021/acs.chemrev.5b00609)
4. [G. Sun, N. Giovambattista, E. G. Wang, and L. Xu\*, et al. Soft Matter 9, 11374 (2013)](https://pubs.rsc.org/en/content/articlelanding/2013/sm/c3sm52206g)
5. [Z. Wu, Y. Chen, W. Wang, W. Kob, L. Xu, Nat. Commun. 14, 2955 (2023)](https://www.nature.com/articles/s41467-023-38547-w)
