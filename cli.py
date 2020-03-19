from ct_pd_scraper.__main__ import main
import sys
import traceback

if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print(f"Exception found: {str(e)}")
        traceback.print_exc()
        input("Press enter to exit")