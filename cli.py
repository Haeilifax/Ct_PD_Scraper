from Ct_PD_Scraper.__main__ import main
import sys
import traceback

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Exception found: {str(e)}")
        traceback.print_exc()
    finally:
        input("Press any key to exit")