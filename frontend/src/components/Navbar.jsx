//Por ahora sin navegacion je

import styles from "./Navbar.module.css";

const tabs = ["Mi Álbum", "Duplicadas", "Faltantes", "Intercambios"];

function Navbar({ tabActiva, onTabChange}) {
    return (
        <nav className={styles.nav}>
            <div className={styles.logo}>
                <span className={styles.logoIcono}>⚽</span>
                <div>
                    <div className={styles.logoNombre}>SwapFigus</div>
                    <div className={styles.logoSub}>FIFA 2026</div>
                </div>
            </div>

            <div className={styles.tabs}>
                {tabs.map((tab) =>(
                    <button
                    key={tab}
                    onClick={() => onTabChange(tab)}
                    className={tab == tabActiva ? styles.tabActiva : styles.tab}
                    >

                        {tab}
                    </button>
                ))}
            </div>
        </nav>
    );
}

export default Navbar;