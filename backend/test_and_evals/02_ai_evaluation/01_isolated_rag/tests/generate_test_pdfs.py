#!/usr/bin/env python3
"""
Generate synthetic test PDFs for the RAG evaluation suite.

Creates two 10-chapter university lecture notes:
  - test_document_en.pdf — "Introduction to Operating Systems"
  - test_document_hu.pdf — "Bevezetés az adatbázis-kezelésbe"

Each document has 10 clearly delineated sections with distinct factual content
designed for unambiguous retrieval testing.

Usage:
    cd backend
    python test_and_evals/02_ai_evaluation/01_isolated_rag/tests/generate_test_pdfs.py
"""

from pathlib import Path
from fpdf import FPDF


# ---------------------------------------------------------------------------
# English document — Introduction to Operating Systems (10 chapters)
# ---------------------------------------------------------------------------

EN_TITLE = "Introduction to Operating Systems"
EN_SECTIONS = [
    (
        "1. Processes and Threads",
        (
            "A process is an instance of a running program. Each process has its own "
            "address space, program counter, stack, and set of open file descriptors. "
            "The operating system kernel maintains a Process Control Block (PCB) for "
            "every active process. The PCB stores the process state (new, ready, running, "
            "waiting, terminated), CPU registers, scheduling information, and memory "
            "management data.\n\n"
            "Threads are lightweight execution units within a process. Unlike processes, "
            "threads share the same address space and resources but maintain their own "
            "stack and program counter. Multi-threaded programs can achieve concurrency "
            "on a single core through time-slicing and true parallelism on multi-core "
            "processors.\n\n"
            "Context switching between processes is expensive because the entire address "
            "space must be swapped, including TLB entries. Context switching between "
            "threads of the same process is cheaper since the shared address space "
            "remains unchanged. The POSIX threads (pthreads) library provides the "
            "standard API for thread creation and synchronization on Unix systems.\n\n"
            "Inter-process communication (IPC) mechanisms include pipes, message queues, "
            "shared memory, and sockets. Pipes provide a unidirectional byte stream "
            "between related processes. Named pipes (FIFOs) extend this to unrelated "
            "processes. Shared memory is the fastest IPC mechanism because data does "
            "not need to be copied between kernel and user space."
        ),
    ),
    (
        "2. CPU Scheduling",
        (
            "CPU scheduling determines which process runs on the processor at any given "
            "time. The scheduler selects from the ready queue using one of several "
            "algorithms. Scheduling can be preemptive, where the OS can interrupt a "
            "running process, or non-preemptive (cooperative), where a process runs "
            "until it voluntarily yields the CPU.\n\n"
            "First-Come, First-Served (FCFS) is the simplest scheduling algorithm. "
            "Processes are executed in the order they arrive in the ready queue. FCFS "
            "suffers from the convoy effect, where short processes wait behind long ones, "
            "leading to high average waiting time.\n\n"
            "Shortest Job First (SJF) selects the process with the smallest expected "
            "CPU burst. SJF is provably optimal for minimizing average waiting time but "
            "requires advance knowledge of burst lengths, which is typically estimated "
            "using exponential averaging of previous bursts.\n\n"
            "Round Robin (RR) assigns each process a fixed time quantum (typically "
            "10-100 milliseconds). When the quantum expires the process is moved to the "
            "back of the ready queue. Smaller quanta improve response time but increase "
            "context switching overhead. A quantum of zero degenerates into processor "
            "sharing.\n\n"
            "Priority scheduling assigns a numerical priority to each process. The "
            "highest priority process runs first. A key problem is starvation, where "
            "low-priority processes may never execute. Aging solves this by gradually "
            "increasing the priority of waiting processes. The Multilevel Feedback Queue "
            "(MLFQ) scheduler combines multiple priority queues with dynamic promotion "
            "and demotion rules."
        ),
    ),
    (
        "3. Memory Management",
        (
            "Memory management is responsible for allocating and deallocating physical "
            "memory to processes. Virtual memory allows each process to have a large, "
            "contiguous address space independent of the physical memory available.\n\n"
            "Paging divides virtual memory into fixed-size pages (typically 4 KB) and "
            "physical memory into frames of the same size. The page table maps virtual "
            "page numbers to physical frame numbers. A Translation Lookaside Buffer (TLB) "
            "caches recently used page table entries for fast address translation. TLB "
            "miss rates are a critical performance metric.\n\n"
            "When physical memory is full, the OS must choose a page to evict. The "
            "Least Recently Used (LRU) algorithm evicts the page that has not been "
            "accessed for the longest time. LRU is expensive to implement exactly, so "
            "operating systems use approximations such as the Clock algorithm (also "
            "known as Second Chance), which uses a reference bit per page.\n\n"
            "Thrashing occurs when a process spends more time swapping pages than "
            "executing instructions. This happens when the working set of a process "
            "exceeds the available physical memory. The working set model defines the "
            "set of pages actively used by a process within a time window.\n\n"
            "Segmentation divides memory into variable-sized segments based on logical "
            "divisions such as code, data, and stack. Modern systems often combine "
            "segmentation with paging (segmented paging). The x86 architecture supports "
            "both segmentation and paging, although most modern operating systems "
            "minimize the use of segmentation in favor of flat paging."
        ),
    ),
    (
        "4. File Systems",
        (
            "A file system organizes data on persistent storage devices. The key "
            "abstractions are files (named collections of data) and directories "
            "(containers that organize files hierarchically). Every file has associated "
            "metadata stored in an inode on Unix systems, including ownership, "
            "permissions, timestamps, size, and pointers to data blocks.\n\n"
            "Block allocation strategies determine how files are stored on disk. "
            "Contiguous allocation stores files in consecutive blocks, enabling fast "
            "sequential access but causing external fragmentation. Linked allocation "
            "chains disk blocks via pointers, eliminating fragmentation but making "
            "random access slow. Indexed allocation stores all block pointers in a "
            "dedicated index block (the inode in ext4), supporting both sequential "
            "and random access efficiently.\n\n"
            "Journaling file systems such as ext4 and NTFS maintain a write-ahead log "
            "(journal) to ensure consistency after crashes. Before modifying the file "
            "system structure, the intended changes are written to the journal. If a "
            "crash occurs, the journal is replayed during recovery. ext4 supports three "
            "journaling modes: journal (full data), ordered (metadata only, data written "
            "first), and writeback (metadata only, no ordering).\n\n"
            "The Virtual File System (VFS) layer in Linux provides a uniform interface "
            "for different file system implementations. User programs interact with "
            "VFS through system calls (open, read, write, close), and VFS dispatches "
            "these to the appropriate file system driver. This abstraction allows "
            "transparent access to ext4, XFS, NFS, and even pseudo-filesystems like "
            "/proc and /sys."
        ),
    ),
    (
        "5. Deadlocks and Synchronization",
        (
            "A deadlock occurs when two or more processes are permanently blocked, each "
            "waiting for a resource held by another. Four conditions must hold "
            "simultaneously for a deadlock to occur: (1) Mutual exclusion — at least one "
            "resource must be non-shareable; (2) Hold and wait — a process holding a "
            "resource waits for another; (3) No preemption — resources cannot be forcibly "
            "taken; (4) Circular wait — a circular chain of processes exists where each "
            "waits for a resource held by the next.\n\n"
            "Deadlock prevention eliminates one of the four necessary conditions. "
            "Resource ordering prevents circular wait by requiring processes to request "
            "resources in a predetermined order. The Banker's algorithm (Dijkstra, 1965) "
            "dynamically checks whether granting a request leads to a safe state where "
            "all processes can still complete.\n\n"
            "Synchronization primitives coordinate concurrent access to shared resources. "
            "A mutex (mutual exclusion lock) ensures only one thread enters the critical "
            "section at a time. Semaphores generalize mutexes by maintaining a count; a "
            "binary semaphore is equivalent to a mutex, while a counting semaphore "
            "controls access to a resource pool.\n\n"
            "The classic synchronization problems are: the Producer-Consumer problem, "
            "solved with two semaphores (empty and full) and a mutex; the Readers-Writers "
            "problem, which balances concurrent reads with exclusive writes; and the "
            "Dining Philosophers problem, which illustrates deadlock and starvation in "
            "resource allocation. Monitors encapsulate shared data with procedures and "
            "condition variables, providing a higher-level synchronization abstraction "
            "used in languages like Java (synchronized keyword) and Python (threading.Lock)."
        ),
    ),
    (
        "6. I/O Systems",
        (
            "The I/O subsystem manages communication between the CPU and peripheral "
            "devices such as disks, keyboards, network cards, and displays. Device "
            "drivers are kernel modules that translate generic I/O requests into "
            "hardware-specific commands for each device.\n\n"
            "There are three primary I/O techniques. Programmed I/O (polling) requires "
            "the CPU to repeatedly check the device status register, wasting CPU cycles. "
            "Interrupt-driven I/O allows the device to signal the CPU when data is ready "
            "via a hardware interrupt, freeing the CPU to execute other tasks while waiting. "
            "Direct Memory Access (DMA) offloads data transfer entirely to a dedicated "
            "DMA controller, which moves data between device and memory without CPU "
            "involvement, generating only a single interrupt upon completion.\n\n"
            "The I/O scheduler in modern operating systems reorders disk requests to "
            "minimize seek time. The elevator algorithm (SCAN) moves the disk head in "
            "one direction, servicing requests along the way, then reverses. C-SCAN "
            "(Circular SCAN) only services requests in one direction, returning to the "
            "beginning without servicing. The Completely Fair Queueing (CFQ) scheduler "
            "in Linux allocates I/O bandwidth proportionally among processes.\n\n"
            "Buffering and caching are critical for I/O performance. The page cache in "
            "Linux stores recently read disk blocks in memory, serving subsequent reads "
            "from RAM. Write-back caching delays disk writes to batch them efficiently, "
            "while write-through caching writes to both cache and disk simultaneously "
            "for greater reliability at the cost of latency."
        ),
    ),
    (
        "7. Virtualization",
        (
            "Virtualization allows multiple operating systems to run concurrently on a "
            "single physical machine. A hypervisor (virtual machine monitor) mediates "
            "access to hardware resources. Type 1 hypervisors (bare-metal) run directly "
            "on hardware — examples include VMware ESXi, Microsoft Hyper-V, and Xen. "
            "Type 2 hypervisors (hosted) run as applications on a host operating system "
            "— examples include VirtualBox and VMware Workstation.\n\n"
            "Hardware-assisted virtualization (Intel VT-x, AMD-V) adds CPU instructions "
            "that allow the hypervisor to trap privileged guest operations efficiently. "
            "Before hardware support, full virtualization relied on binary translation, "
            "which dynamically rewrote sensitive guest instructions. Paravirtualization "
            "(used by Xen) modifies the guest OS to call hypervisor APIs (hypercalls) "
            "instead of executing privileged instructions directly.\n\n"
            "Memory virtualization uses Extended Page Tables (EPT on Intel) or Nested "
            "Page Tables (NPT on AMD) to translate guest virtual addresses to host "
            "physical addresses without hypervisor intervention on every page fault. "
            "Memory ballooning reclaims unused guest memory by inflating a balloon "
            "driver inside the guest, forcing it to release pages back to the host.\n\n"
            "Containers (Docker, LXC) provide OS-level virtualization using Linux "
            "namespaces and cgroups. Unlike VMs, containers share the host kernel and "
            "have near-native performance. Namespaces isolate process IDs, network "
            "stacks, mount points, and user IDs. Cgroups limit CPU, memory, and I/O "
            "bandwidth per container."
        ),
    ),
    (
        "8. Security and Protection",
        (
            "Operating system security relies on multiple mechanisms working together. "
            "Access control determines which subjects (users, processes) can perform "
            "which operations on which objects (files, devices). Discretionary Access "
            "Control (DAC) lets file owners set permissions — the Unix rwxrwxrwx model "
            "assigns read, write, and execute bits for owner, group, and others.\n\n"
            "Mandatory Access Control (MAC) enforces system-wide policies that override "
            "owner preferences. SELinux (Security-Enhanced Linux) implements MAC using "
            "security contexts and type enforcement rules. AppArmor provides a simpler "
            "path-based MAC alternative. The principle of least privilege dictates that "
            "programs should operate with the minimum permissions necessary.\n\n"
            "User authentication verifies identity. The /etc/shadow file on Linux stores "
            "salted password hashes using algorithms like bcrypt (cost factor 12 by "
            "default) or SHA-512. Multi-factor authentication combines something you "
            "know (password), something you have (token), and something you are "
            "(biometrics). Pluggable Authentication Modules (PAM) provide a flexible "
            "framework for configuring authentication methods.\n\n"
            "Buffer overflow attacks exploit programs that write beyond allocated memory "
            "bounds. Stack canaries detect overflows by placing a known value before the "
            "return address. Address Space Layout Randomization (ASLR) randomizes memory "
            "layout to prevent predictable exploits. Data Execution Prevention (DEP) "
            "marks memory pages as non-executable to prevent code injection. Together "
            "these defenses form a layered security model."
        ),
    ),
    (
        "9. Distributed Systems",
        (
            "A distributed system consists of multiple autonomous computers connected "
            "by a network that coordinate to appear as a single coherent system. The "
            "key challenges are partial failure (some nodes crash while others continue), "
            "network partitions, and the absence of a global clock.\n\n"
            "The CAP theorem (Brewer, 2000) states that a distributed data store can "
            "provide at most two of three guarantees simultaneously: Consistency (all "
            "nodes see the same data), Availability (every request receives a response), "
            "and Partition tolerance (the system operates despite network splits). In "
            "practice, partition tolerance is unavoidable, so systems choose between "
            "CP (consistent but may be unavailable) and AP (available but may return "
            "stale data).\n\n"
            "Consensus protocols ensure agreement among distributed nodes. Paxos "
            "(Lamport, 1998) guarantees safety but may not terminate under certain "
            "network conditions. Raft (Ongaro, 2014) provides an equivalent guarantee "
            "with a more understandable leader-based approach: a leader is elected, "
            "accepts log entries, and replicates them to followers. A majority quorum "
            "is required for commits.\n\n"
            "Remote Procedure Call (RPC) enables a program on one machine to execute "
            "a procedure on another machine transparently. gRPC (Google, 2015) uses "
            "Protocol Buffers for serialization and HTTP/2 for transport, supporting "
            "unary, server-streaming, client-streaming, and bidirectional streaming "
            "patterns. Service discovery mechanisms like DNS, Consul, or etcd allow "
            "clients to locate services dynamically."
        ),
    ),
    (
        "10. Storage Management",
        (
            "Storage management encompasses disk scheduling, RAID configurations, and "
            "modern storage technologies. Hard disk drives (HDDs) store data on rotating "
            "magnetic platters with access times of 5-10 milliseconds. Solid-state drives "
            "(SSDs) use NAND flash memory with access times under 100 microseconds — "
            "roughly 100x faster than HDDs for random reads.\n\n"
            "RAID (Redundant Array of Independent Disks) combines multiple drives for "
            "performance and/or reliability. RAID 0 stripes data across drives for speed "
            "but offers no redundancy. RAID 1 mirrors data for fault tolerance at the "
            "cost of halving usable capacity. RAID 5 distributes parity across drives, "
            "tolerating one drive failure. RAID 6 extends this with double parity, "
            "tolerating two simultaneous drive failures. RAID 10 combines mirroring and "
            "striping for both performance and redundancy.\n\n"
            "Logical Volume Manager (LVM) on Linux provides an abstraction layer between "
            "physical disks and file systems. Physical volumes (PVs) are grouped into "
            "volume groups (VGs), which are divided into logical volumes (LVs). LVM "
            "supports dynamic resizing, snapshotting, and thin provisioning.\n\n"
            "Modern storage follows the NVMe (Non-Volatile Memory Express) protocol, "
            "which replaces the legacy AHCI/SATA interface. NVMe communicates directly "
            "over PCIe lanes with up to 65,535 I/O queues, each supporting 65,536 "
            "commands. This parallelism allows NVMe SSDs to achieve sequential read "
            "speeds exceeding 7,000 MB/s and IOPS (Input/Output Operations Per Second) "
            "above 1,000,000 for random 4K reads."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Hungarian document — Bevezetés az adatbázis-kezelésbe (10 chapters)
# ---------------------------------------------------------------------------

HU_TITLE = "Bevezetés az adatbázis-kezelésbe"
HU_SECTIONS = [
    (
        "1. A relációs adatmodell",
        (
            "Az adatbázis-kezelő rendszer (DBMS) szervezett adatgyűjteményt kezel. "
            "A relációs modellt Edgar F. Codd javasolta 1970-ben. A modell alapegysége "
            "a reláció (tábla), amely sorokból (rekordokból) és oszlopokból "
            "(attribútumokból) áll. Minden sornak egyedinek kell lennie, amit az "
            "elsődleges kulcs (primary key) biztosít.\n\n"
            "Az idegen kulcs (foreign key) egy másik tábla elsődleges kulcsára hivatkozik, "
            "ezzel biztosítva a referenciális integritást. Például egy 'Megrendelések' "
            "tábla 'ügyfél_id' oszlopa az 'Ügyfelek' tábla 'id' oszlopára mutat. "
            "Ha egy ügyfelet törölni próbálunk, akihez tartozik megrendelés, a DBMS "
            "elutasítja a műveletet (ON DELETE RESTRICT) vagy kaszkád módon törli a "
            "kapcsolódó sorokat (ON DELETE CASCADE).\n\n"
            "A reláció sémája (schema) meghatározza a tábla szerkezetét: az attribútumok "
            "neveit és típusait. A séma idővel ritkán változik (DDL műveletek), míg a "
            "séma példánya (instance) — azaz a konkrét adatok — folyamatosan módosul "
            "(DML műveletek). A relációs algebra műveletek (szelekció, projekció, "
            "természetes összekapcsolás, unió, különbség) formális alapot adnak az "
            "adatlekérdezéshez.\n\n"
            "A NULL érték speciális: azt jelenti, hogy az adat ismeretlen vagy nem "
            "alkalmazható. A háromértékű logika (TRUE, FALSE, UNKNOWN) szabályai szerint "
            "NULL = NULL kiértékelése UNKNOWN, nem TRUE. Ezért az IS NULL és IS NOT NULL "
            "operátorok szükségesek az összehasonlításhoz."
        ),
    ),
    (
        "2. SQL alapok",
        (
            "A Structured Query Language (SQL) a relációs adatbázisok szabványos nyelve. "
            "A DML (Data Manipulation Language) részei: SELECT, INSERT, UPDATE, DELETE. "
            "A DDL (Data Definition Language) részei: CREATE TABLE, ALTER TABLE, DROP TABLE.\n\n"
            "A SELECT utasítás felépítése: SELECT oszloplista FROM tábla WHERE feltétel "
            "GROUP BY csoportosító_oszlop HAVING csoport_feltétel ORDER BY rendező_oszlop. "
            "Az aggregáló függvények (COUNT, SUM, AVG, MIN, MAX) a GROUP BY-jal együtt "
            "működnek. A HAVING záradék az aggregált csoportokat szűri, míg a WHERE az "
            "egyedi sorokat.\n\n"
            "Az összekapcsolás (JOIN) két tábla sorait párosítja. INNER JOIN csak az "
            "egyező sorokat adja vissza. LEFT OUTER JOIN a bal oldali tábla minden sorát "
            "megtartja, és NULL-t ad a jobb oldalon, ha nincs egyezés. CROSS JOIN a "
            "Descartes-szorzatot képezi. A természetes összekapcsolás (NATURAL JOIN) "
            "automatikusan az azonos nevű oszlopok alapján kapcsol.\n\n"
            "Az allekérdezések (subqueries) beágyazott SELECT utasítások. Korrelált "
            "allekérdezés esetén a belső lekérdezés hivatkozik a külső lekérdezés "
            "oszlopaira. Az EXISTS operátor ellenőrzi, hogy az allekérdezés legalább "
            "egy sort visszaad-e. Az IN operátor egy értékhalmazban keres.\n\n"
            "A nézetek (VIEW) virtuális táblák, amelyek egy tárolt SELECT utasítás "
            "eredményét reprezentálják. A materializált nézet (MATERIALIZED VIEW) fizikailag "
            "is eltárolja az eredményt, így gyorsabb lekérdezést tesz lehetővé, de "
            "frissíteni kell az alaptáblák változásakor."
        ),
    ),
    (
        "3. Normalizálás",
        (
            "A normalizálás célja a redundancia csökkentése és az adatintegritás "
            "biztosítása. A funkcionális függőség (FD) azt fejezi ki, hogy egy "
            "attribútumhalmaz (A) egyértelműen meghatároz egy másikat (B): A → B.\n\n"
            "Az első normálforma (1NF) megköveteli, hogy minden attribútum atomi "
            "értéket tartalmazzon — nem lehet benne lista vagy beágyazott tábla. "
            "A második normálforma (2NF) az 1NF-en felül megköveteli, hogy minden "
            "nem-kulcs attribútum a teljes elsődleges kulcstól függjön, nem csak "
            "annak egy részétől (nincs parciális függőség).\n\n"
            "A harmadik normálforma (3NF) a 2NF-en felül kizárja a tranzitív "
            "függőségeket: ha A → B és B → C, akkor A → C tranzitív, és C-t külön "
            "táblába kell szervezni. A Boyce-Codd normálforma (BCNF) szigorúbb: "
            "minden nem-triviális FD bal oldalának szuperkulcsnak kell lennie.\n\n"
            "A denormalizálás tudatos döntés: teljesítményi okokból szándékosan "
            "redundanciát vezetünk be. Például egy rendelés táblába közvetlenül "
            "beszúrhatjuk az ügyfél nevét, hogy elkerüljük a gyakori JOIN műveleteket. "
            "Az OLAP (Online Analytical Processing) rendszerek često használnak "
            "denormalizált csillagsémát (star schema) vagy hópehelysémát (snowflake "
            "schema) a gyors analitikai lekérdezésekhez.\n\n"
            "A többértékű függőségek (MVD) és a negyedik normálforma (4NF) a "
            "bonyolultabb redundancia-típusokat kezelik. A gyakorlatban a 3NF vagy "
            "BCNF elérése általában elegendő a legtöbb alkalmazáshoz."
        ),
    ),
    (
        "4. Tranzakciókezelés",
        (
            "A tranzakció logikailag összetartozó adatbázis-műveletek sorozata, amely "
            "az ACID tulajdonságokat garantálja. Atomicitás (Atomicity): a tranzakció "
            "vagy teljes egészében végrehajtódik, vagy egyáltalán nem. Konzisztencia "
            "(Consistency): a tranzakció az adatbázist egyik érvényes állapotból egy "
            "másik érvényes állapotba viszi. Izoláció (Isolation): egyidejű tranzakciók "
            "nem zavarják egymást. Tartósság (Durability): a véglegesített (committed) "
            "változások túlélik a rendszerhibákat.\n\n"
            "Az izolációs szintek (SQL szabvány): READ UNCOMMITTED lehetővé teszi a "
            "piszkos olvasást (dirty read). READ COMMITTED megakadályozza a piszkos "
            "olvasást, de nem véd a nem-megismételhető olvasás (non-repeatable read) "
            "ellen. REPEATABLE READ garantálja, hogy ugyanaz a lekérdezés mindig "
            "ugyanazokat a sorokat adja vissza, de fantom sorok (phantom reads) "
            "megjelenhetnek. SERIALIZABLE a legszigorúbb szint, amely teljes izolációt "
            "biztosít soros végrehajtás szimulálásával.\n\n"
            "A kétfázisú zárolás (2PL — Two-Phase Locking) protokoll két szakaszból áll: "
            "növekvő fázis (zárak megszerzése) és csökkenő fázis (zárak elengedése). "
            "A szigorú 2PL (Strict 2PL) az összes írási zárat a tranzakció végéig "
            "tartja, ezzel megakadályozva a kaszkád visszagörgetést.\n\n"
            "A helyreállítás a Write-Ahead Logging (WAL) elvére épül: minden módosítás "
            "előtt egy naplóbejegyzés kerül a naplófájlba. A REDO napló a véglegesített "
            "de lemezre nem írt változtatásokat ismétli meg. Az UNDO napló a félbeszakadt "
            "tranzakciókat vonja vissza. Az ARIES (Algorithm for Recovery and Isolation "
            "Exploiting Semantics) a legelterjedtebb WAL-alapú helyreállítási algoritmus."
        ),
    ),
    (
        "5. Indexelés és lekérdezés-optimalizálás",
        (
            "Az index egy kiegészítő adatszerkezet, amely felgyorsítja a keresést. "
            "A B+ fa a legelterjedtebb indexstruktúra a relációs adatbázisokban. "
            "A B+ fa levélcsomópontjai láncolt listát alkotnak, ami hatékony "
            "tartomány-lekérdezéseket (range query) tesz lehetővé. Tipikus elágazási "
            "tényező: 100-500, és három szintű B+ fa akár egymilliárd rekordot is "
            "indexelhet.\n\n"
            "A hash index pontos egyezés (point query) keresésre optimális, de nem "
            "támogatja a tartomány-lekérdezéseket. Statikus hashelnél a vödrök száma "
            "fix; dinamikus módszerek — kiterjeszthető hashing (extendible hashing) "
            "és lineáris hashing — alkalmazkodnak az adatmennyiség változásához.\n\n"
            "Az összetett index (composite index) több oszlopot tartalmaz. Az oszlopok "
            "sorrendje kritikus: egy (A, B, C) index hatékonyan támogatja az A, (A,B), "
            "és (A,B,C) szűréseket, de nem hatékony B vagy C önálló szűrésére. "
            "Ezt nevezzük legbaloldalibb előtag szabálynak (leftmost prefix rule).\n\n"
            "A lekérdezés-optimalizáló (query optimizer) választja ki a végrehajtási "
            "tervet. Költségalapú optimalizálás (cost-based optimization) során a "
            "rendszer statisztikákat használ (táblaméret, oszlop-kardinalitás, "
            "hisztogramok) a különböző tervek becsült költségének összehasonlítására. "
            "Az EXPLAIN utasítás megmutatja a választott tervet. Gyakori optimalizálási "
            "stratégiák: index scan vs. full table scan, nested loop join vs. hash join "
            "vs. sort-merge join.\n\n"
            "A fedő index (covering index) minden szükséges oszlopot tartalmaz, így "
            "a lekérdezés kizárólag az indexből szolgálható ki, a tábla adatlapjainak "
            "olvasása nélkül (index-only scan). Ez drámaian csökkentheti az I/O műveletek "
            "számát."
        ),
    ),
    (
        "6. Adatbázis-tervezés és ER-modellezés",
        (
            "Az adatbázis-tervezés első lépése a koncepcionális modell elkészítése. "
            "Az Egyed-Kapcsolat (ER — Entity-Relationship) diagram a valós világ "
            "objektumait és azok kapcsolatait ábrázolja. Az egyedtípus (entity type) "
            "egy valós világ objektumát reprezentálja (pl. Hallgató, Kurzus), az "
            "attribútumok az egyed tulajdonságait írják le (pl. név, neptun_kód).\n\n"
            "A kapcsolattípusok (relationship types) lehetnek egy-egy (1:1), egy-több "
            "(1:N), vagy több-több (M:N). Egy-egy kapcsolat például az Állampolgár és "
            "Útlevél között áll fenn. Egy-több kapcsolat a Tanszék és Oktató között: "
            "egy tanszékhez több oktató tartozik, de egy oktató csak egy tanszéken "
            "dolgozik. Több-több kapcsolat a Hallgató és Kurzus között: egy hallgató "
            "több kurzust vesz fel, és egy kurzusra több hallgató jár.\n\n"
            "A gyenge egyed (weak entity) nem rendelkezik saját egyedi azonosítóval, "
            "létezése egy erős egyedtől függ. Például a Szoba egyed önmagában nem "
            "egyedi (több épületben is lehet 101-es szoba), csak az Épület egyeddel "
            "együtt azonosítható. A specializáció és generalizáció öröklési "
            "hierarchiát hoz létre: egy Személy egyed specializálható Hallgató és "
            "Oktató alegyedekre.\n\n"
            "A koncepcionális modellből relációs séma készül. Az M:N kapcsolat mindig "
            "külön kapcsolótáblát (junction table) igényel. Az 1:N kapcsolat az idegen "
            "kulcs elhelyezésével a 'sok' oldali táblában oldható meg. Az ER-diagram "
            "transzformációja a relációs modellbe formalizált szabályok szerint történik, "
            "amelyet Chen (1976) írt le először."
        ),
    ),
    (
        "7. Elosztott adatbázisok",
        (
            "Az elosztott adatbázis-kezelő rendszer (DDBMS) az adatokat több fizikailag "
            "különálló csomóponton tárolja. Az elosztás lehet homogén (minden csomópont "
            "ugyanazt a DBMS-t futtatja) vagy heterogén (különböző DBMS-ek, pl. "
            "MySQL és PostgreSQL).\n\n"
            "A fragmentálás az adatok felosztását jelenti a csomópontok között. "
            "Horizontális fragmentálás (sharding) a tábla sorait osztja szét — például "
            "európai ügyfelek az EU szerveren, amerikai ügyfelek az US szerveren. "
            "Vertikális fragmentálás a tábla oszlopait választja szét. A replikáció "
            "az adatok másolása több csomópontra a rendelkezésre állás és a "
            "lekérdezési teljesítmény növelése érdekében.\n\n"
            "A kétfázisú véglegesítés (2PC — Two-Phase Commit) protokoll biztosítja "
            "az elosztott tranzakciók atomicitását. Az első fázisban a koordinátor "
            "megkérdezi a résztvevőket (PREPARE), a második fázisban döntés születik "
            "(COMMIT vagy ABORT). Ha bármelyik résztvevő nemmel szavaz, az egész "
            "tranzakció visszagörgetődik. A 2PC hátránya a blokkoló természete: ha "
            "a koordinátor meghibásodik a döntés előtt, a résztvevők határozatlan "
            "állapotban maradhatnak.\n\n"
            "A CAP-tétel (Brewer, 2000) szerint egy elosztott rendszer a konzisztencia "
            "(Consistency), rendelkezésre állás (Availability) és partíciótűrés "
            "(Partition tolerance) közül egyszerre csak kettőt garantálhat. A BASE "
            "modell (Basically Available, Soft state, Eventually consistent) lazább "
            "konzisztenciát kínál magas rendelkezésre állás mellett."
        ),
    ),
    (
        "8. NoSQL adatbázisok",
        (
            "A NoSQL adatbázisok a relációs modell alternatívái, amelyeket nagy "
            "adatmennyiség, magas rendelkezésre állás és rugalmas séma igénye hívott "
            "életre. Négy fő típus létezik.\n\n"
            "A kulcs-érték tárolók (key-value stores) az adatokat egyszerű kulcs-érték "
            "párokként kezelik. A Redis memóriában tárolja az adatokat, 100,000+ "
            "művelet/másodperc sebességgel. Tipikus felhasználás: munkamenet-kezelés "
            "(session store), gyorsítótárazás (caching), és valós idejű ranglisták. "
            "A DynamoDB (Amazon) elosztott kulcs-érték tároló, amely automatikus "
            "particionálást és replikációt biztosít.\n\n"
            "A dokumentum-orientált adatbázisok (MongoDB, CouchDB) JSON-szerű "
            "dokumentumokat tárolnak. Nincs fix séma — különböző dokumentumok eltérő "
            "mezőkkel rendelkezhetnek. A MongoDB az adatokat BSON (Binary JSON) "
            "formátumban tárolja, és támogatja a beágyazott dokumentumokat és tömböket. "
            "Az aggregációs pipeline lehetővé teszi komplex adatfeldolgozást "
            "adatbázisszinten.\n\n"
            "Az oszloporientált adatbázisok (Apache Cassandra, HBase) az adatokat "
            "oszlopcsaládokba szervezik. A Cassandra peer-to-peer architektúrát használ, "
            "nincs egyetlen hibapontja (single point of failure), és lineárisan "
            "skálázodik. A gráfadatbázisok (Neo4j, Amazon Neptune) csomópontokból "
            "és élekből álló gráfként modellezik az adatokat. Ideálisak szociális "
            "hálózatok, ajánlórendszerek és tudásgráfok számára."
        ),
    ),
    (
        "9. Adatbázis-biztonság",
        (
            "Az adatbázis-biztonság három alappillére: bizalmasság (confidentiality), "
            "integritás (integrity) és rendelkezésre állás (availability) — az ún. "
            "CIA-triász. Az SQL jogosultságkezelés a GRANT és REVOKE utasításokkal "
            "működik. A GRANT SELECT ON tábla TO felhasználó olvasási jogot ad, "
            "a REVOKE visszavonja azt.\n\n"
            "A szerepkör-alapú hozzáférés-vezérlés (RBAC — Role-Based Access Control) "
            "a jogosultságokat szerepkörökhöz rendeli, nem közvetlenül felhasználókhoz. "
            "Egy 'olvasó' szerepkör csak SELECT jogot kap, egy 'szerkesztő' SELECT "
            "és UPDATE jogot, míg az 'admin' teljes DBA jogosultságot. Ez egyszerűsíti "
            "a jogosultságok kezelését nagy szervezetekben.\n\n"
            "Az SQL injection a legelterjedtebb adatbázis-támadási technika. A támadó "
            "rosszindulatú SQL kódot juttat be a felhasználói bemeneten keresztül. "
            "Például: ' OR 1=1 -- egy bejelentkezési űrlapon megkerülheti az "
            "autentikációt. A védekezés elsődleges módja a paraméteres lekérdezés "
            "(prepared statement), ahol a felhasználói bemenet soha nem kerül "
            "közvetlenül az SQL utasításba.\n\n"
            "Az adattitkosítás két szinten működik. A tárolt adatok titkosítása "
            "(encryption at rest) a lemezen tárolt adatokat védi — a Transparent Data "
            "Encryption (TDE) például az Oracle és SQL Server rendszerekben automatikusan "
            "titkosítja az adatfájlokat. Az átvitel közbeni titkosítás (encryption in "
            "transit) SSL/TLS protokollal védi a kliens és szerver közötti kommunikációt."
        ),
    ),
    (
        "10. Adattárházak és OLAP",
        (
            "Az adattárház (data warehouse) elemzési célra optimalizált adatbázis, "
            "amely különböző operatív forrásokból (OLTP rendszerek) összegyűjtött "
            "adatokat tárol. Az ETL (Extract, Transform, Load) folyamat kinyeri az "
            "adatokat a forrásrendszerekből, átalakítja az egységes formátumba, "
            "és betölti az adattárházba.\n\n"
            "A dimenzionális modellezés az adattárház leggyakoribb tervezési módszere. "
            "A csillagséma (star schema) egy központi ténytáblából (fact table) és "
            "a hozzá kapcsolódó dimenziótáblákból (dimension tables) áll. A ténytábla "
            "tartalmazza a mérhető adatokat (pl. eladási összeg, darabszám), míg a "
            "dimenziótáblák a kontextust adják (idő, termék, bolt, ügyfél). A "
            "hópehelyséma (snowflake schema) a dimenziótáblákat tovább normalizálja.\n\n"
            "Az OLAP (Online Analytical Processing) műveletek a többdimenziós "
            "adatelemzést támogatják. A roll-up aggregálja az adatokat (pl. napi "
            "szintről havi szintre). A drill-down részletezi (havi → napi). A slice "
            "egy dimenziót rögzít (pl. csak 2024-es adatok). A dice több dimenziót "
            "szűr egyszerre. A pivot elforgatja a nézetet.\n\n"
            "A modern adattárház-megoldások felhőalapúak. A Snowflake szétválasztja "
            "a számítást és a tárolást, így azok egymástól függetlenül skálázhatók. "
            "A Google BigQuery szerver nélküli (serverless) architektúrát kínál, "
            "oszloporientált tárolással és automatikus optimalizálással. Az Apache "
            "Spark és a dbt (data build tool) az adattárház-feletti transzformációk "
            "és modellezés népszerű eszközei."
        ),
    ),
]


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------


def build_pdf(title: str, sections: list, output_path: Path) -> None:
    """Build a multi-page PDF with title + sections."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Use built-in Helvetica — it has Latin-2 glyph coverage when using
    # latin-1 encoding which covers most Hungarian characters.
    # For full UTF-8 we'd need to add a TTF font.
    # Instead, we'll add a Unicode font.

    # Add a Unicode font for Hungarian characters
    # fpdf2 has built-in support for standard fonts only; for full UTF-8 we
    # use the add_font with a TTF file. We'll use DejaVu which is commonly
    # available on Linux.
    import shutil

    dejavu_path = shutil.which("fc-list")  # just checking system fonts exist
    # Try common paths for DejaVuSans
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]

    font_path = None
    for candidate in font_candidates:
        if Path(candidate).exists():
            font_path = candidate
            break

    if font_path:
        pdf.add_font("DejaVu", "", font_path)
        pdf.add_font(
            "DejaVu", "B", font_path.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
        )
        body_font = "DejaVu"
    else:
        # Fallback — will have limited Hungarian char support
        body_font = "Helvetica"
        print(
            f"  WARNING: DejaVuSans.ttf not found, falling back to Helvetica (limited Hungarian chars)"
        )

    # Title page
    pdf.add_page()
    pdf.set_font(body_font, "B", 20)
    pdf.cell(0, 40, title, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font(body_font, "", 11)
    pdf.cell(
        0,
        10,
        "University Lecture Notes — Test Document for RAG Evaluation",
        new_x="LMARGIN",
        new_y="NEXT",
        align="C",
    )
    pdf.ln(10)

    # Sections — each starts on a new page
    for heading, body in sections:
        pdf.add_page()
        pdf.set_font(body_font, "B", 14)
        pdf.cell(0, 10, heading, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.set_font(body_font, "", 10)
        pdf.multi_cell(0, 5.5, body)

    pdf.output(str(output_path))
    print(f"  Created: {output_path}  ({output_path.stat().st_size:,} bytes)")


def main():
    out_dir = Path(__file__).parent / "artifacts"
    out_dir.mkdir(exist_ok=True)
    print("Generating synthetic test PDFs for RAG evaluation...\n")

    build_pdf(EN_TITLE, EN_SECTIONS, out_dir / "test_document_en.pdf")
    build_pdf(HU_TITLE, HU_SECTIONS, out_dir / "test_document_hu.pdf")

    print("\nDone. Now run generate_ground_truth.py to dump chunk mappings.")


if __name__ == "__main__":
    main()
